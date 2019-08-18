# encoding: utf-8
import base64
import smtplib
from email.mime.text import MIMEText

import requests
from flask import Blueprint, request, jsonify, session, json, redirect, url_for

import RGUIController
import User.RGOpenIdController
from Model import user, tokens
from RGIgnoreConfig.RGGlobalConfigContext import RGFullThisServerHost
from RGUtil import RGTimeUtil
from RGUtil.RGCodeUtil import RGResCode, RGVerifyType
from RGUtil.RGRequestHelp import get_data_with_request, form_res, request_value

RestRouter = Blueprint('RGUser', __name__, url_prefix='/user', static_folder='../static')

RGUserLogoutLastPath = '/logout'
RGUserLogoutPath = 'user/' + RGUserLogoutLastPath


with open('RGIgnoreConfig/RGMailAccount.json', 'r') as f:
    RGMailConfig = json.loads(f.read())

"""
page
"""


@RestRouter.route('/friends', methods=["GET"])
@RGUIController.auth_handler(page=True)
def friend_page(user_id):
    t = get_data_with_request(request)
    page = t['page'] if 'page' in t else 0
    size = t['size'] if 'size' in t else 10

    list, page_count, now_page, page_size, count = user.friend_page_list(user_id, page, size)
    t = {
        "list": list,
        "pageCount": page_count,
        "pageSize": page_size,
        "nowPage": now_page,
        "count": count,
        "user": user.get_user(user_id),
        "home": True,
    }

    return RGUIController.ui_render_template("friends.html", **t)


@RestRouter.route('/set', methods=["GET"])
@RGUIController.auth_handler(page=True)
def set_page(user_id):
    t = {
        "user": user.get_user(user_id, need_icon=True, need_username=True),
    }
    return RGUIController.ui_render_template("setting.html", **t)


@RestRouter.route('/passwordPage', methods=["GET"])
def password_page():
    return RGUIController.ui_render_template("login.html", **{
        'username': request_value(request, key='username', default=''),
        'coll_user_email': True,
        'verify_type': 2
    })


@RestRouter.route('/verifyPage', methods=["GET"])
def verify_page():
    username = request_value(request, 'username')

    if username is None:
        return redirect(url_for('login_page'))

    _user = user.get_user_with_username(username, need_email=True)

    if _user is None:
        return redirect(url_for('login_page'))

    verify_type = _user.get_payload(key='type')

    if _user.is_full_active() and verify_type != RGVerifyType.forget_pwd:
        return redirect(url_for('login_page'))
    elif _user.is_active_and_need_bind_email():
        return redirect(url_for('login_page'))
    elif _user.is_time_out():
        return redirect(url_for('login_page'))

    email = _user.get_payload(key='email')
    if email is None:
        return redirect(url_for('login_page'))

    return RGUIController.ui_render_template("login.html", **{
        'username': username,
        'email': email,
        'coll_pwd': True,
        'verify_type': verify_type
    })


"""
restful
"""


@RestRouter.route('/check', methods=['GET'])
def user_check():
    username = request_value(request, 'username', default=None)
    if username is None:
        return jsonify(form_res(RGResCode.lack_param))

    exist = False
    _user = user.login_sign_check(username)
    if _user is None:
        code, _users = User.RGOpenIdController.user_list(username)
        if code == RGResCode.ok and len(_users) > 0:
            exist = True
    else:
        exist = True
    code = RGResCode.ok if exist else RGResCode.not_existed
    return jsonify(form_res(code, _user))


@RestRouter.route('/getVerifyCode', methods=['POST'])
def get_verify_code():
    username = request_value(request, 'username')
    email = request_value(request, 'email')
    verify_type = int(request_value(request, 'verifyType', default='0'))

    if verify_type == RGVerifyType.bind:
        auth, user_id, pass_email, auth_username = RGUIController.do_auth_more_info(need_request_email=False)
        if auth is False or username != auth_username:
            return jsonify(form_res(RGResCode.auth_fail))

    verify_code = user.generate_verify_code()

    res = user.new_user_and_save_verify_code(
        username=username,
        email=email,
        verify_code=verify_code,
        verify_type=verify_type
    )

    if res == RGResCode.ok:
        try:
            if verify_type == RGVerifyType.forget_pwd:
                title = RGMailConfig['newPasswordUserMailTitle']
                content = RGMailConfig['newPasswordVerifyCodeMailFormat'].format(verify_code)
            else:
                title = RGMailConfig['newUserMailTitle']
                content = RGMailConfig['bindVerifyCodeMailFormat'].format(verify_code)

            send_verify_mail(receiver=email, title=title, content=content)
            return jsonify(form_res(RGResCode.ok))
        except Exception as e:
            print(e)
            user.update_user_info(username=username, info_payload='')
            return jsonify(form_res(RGResCode.server_error))
    return jsonify(form_res(res))


@RestRouter.route('/new', methods=['POST'])
def user_new():
    username = request_value(request, 'username')
    # email = request_value(request, 'email')
    pwd = request_value(request, 'pwd')
    verify_code = int(request_value(request, 'code', default='0'))

    uid, res = user.verify_user(
        username=username,
        email=None,
        pwd=pwd,
        verify_code=verify_code,
        verify_type=RGVerifyType.new
    )

    if uid is not None:
        _user = user.get_user_with_username(username=username, need_email=True)
        remember = int(request_value(request, 'remember', default='0'))
        token_type = int(request_value(request, 'type', default='0'))
        token = RGUIController.token_session(
            uid=uid,
            token_type=token_type,
            username=username,
            email=_user.email,
            remember=remember
        )
        return jsonify(form_res(RGResCode.ok, {
            'token': token
        }))
    else:
        return jsonify(form_res(res, None))


@RestRouter.route('/password', methods=['POST'])
def user_password():
    username = request_value(request, 'username')
    pwd = request_value(request, 'pwd')
    verify_code = int(request_value(request, 'code', default='0'))

    uid, res = user.verify_user(
        username=username,
        email=None,
        pwd=pwd,
        verify_code=verify_code,
        verify_type=RGVerifyType.forget_pwd
    )

    if uid is not None:
        _user = user.get_user_with_username(username=username, need_email=True)
        remember = int(request_value(request, 'remember', default='0'))
        token_type = int(request_value(request, 'type', default='0'))
        token = RGUIController.token_session(
            uid=uid,
            token_type=token_type,
            username=username,
            email=_user.email,
            remember=remember
        )
        return jsonify(form_res(RGResCode.ok, {
            'token': token
        }))
    else:
        return jsonify(form_res(res, None))


@RestRouter.route('/bind', methods=['POST'])
def user_bind():
    verify_code = int(request_value(request, 'code'))
    pwd = request_value(request, 'pwd')
    email = request_value(request, 'email')
    username = request_value(request, 'username')

    auth, user_id, pass_email, auth_username = RGUIController.do_auth_more_info(need_request_email=False)
    if not auth or username != auth_username:
        return jsonify(form_res(RGResCode.auth_fail))

    uid, res = user.verify_user(
        username=username,
        email=email,
        pwd=pwd,
        verify_code=verify_code,
        verify_type=RGVerifyType.bind
    )

    if uid is not None:
        token = RGUIController.token_session(
            uid=uid,
            token_type=session['type'],
            username=username,
            email=email,
            remember=None
        )
        return jsonify(form_res(RGResCode.ok, {
            'token': token
        }))
    else:
        return jsonify(form_res(res, None))


def get_username_email(info, has_expire=False):
    info = str(base64.b64decode(info), "utf-8")
    salt = user.salt + ' '

    if has_expire:
        index = info.rfind(' ')
        expire = info[index + 1:]
        expire = int(expire)
        if expire < RGTimeUtil.timestamp():
            return None, None
        info = info[0:index]

    index = info.rfind(salt)
    if index == -1:
        return None, None

    username = info[0:index]
    email = info[index + len(salt):]
    return username, email


def get_base64_username_email(username, email, expire=None):
    if expire is None:
        info = username + user.salt + ' ' + email
    else:
        info = username + user.salt + ' ' + email + ' {}'.format(RGTimeUtil.timestamp() + expire * 1000)
    info = info.encode("utf-8")
    info = base64.urlsafe_b64encode(info)
    info = str(info, encoding="utf-8")
    return info


@RestRouter.route('/login', methods=['POST'])
def user_login():
    username = request_value(request, 'username')
    pwd = request_value(request, 'pwd')
    _user = user.user_login(username, pwd)

    remember = int(request_value(request, 'remember', default='0'))
    token_type = int(request_value(request, 'type', default='0'))

    if _user is not None:
        token = RGUIController.token_session(
            uid=_user.ID,
            token_type=token_type,
            username=_user.username,
            email=_user.email,
            remember=remember
        )
        resp = jsonify(form_res(RGResCode.ok, {
            'token': token
        }))
        return resp
    else:
        return jsonify(form_res(RGResCode.not_existed, None))


@RestRouter.route(RGUserLogoutLastPath, methods=['POST'])
@RGUIController.auth_handler(page=False)
def user_logout(user_id):
    t = get_data_with_request(request)
    token_type = int(t['type'])

    result = tokens.destroy_token(user_id=user_id, token_type=token_type)

    if result:
        RGUIController.token_session_remove()
        return jsonify(form_res(RGResCode.ok, None))
    else:
        return jsonify(form_res(RGResCode.del_fail, None))


@RestRouter.route('/follow', methods=['POST'])
@RGUIController.auth_handler(page=False)
def user_follow(user_id):
    t = get_data_with_request(request)

    other_id = int(t['id'])
    flag, relation = user.follow(user_id, t['id'])

    if flag is True:
        code = RGResCode.ok
        data = {
            'relation': relation,
            're_relation': user.get_relation(other_id, user_id),
        }
    else:
        code = RGResCode.insert_fail
        data = None
    return jsonify(form_res(code, data))


@RestRouter.route('/unfollow', methods=['POST'])
@RGUIController.auth_handler(page=False)
def cancel_follow(user_id):
    t = get_data_with_request(request)

    flag, relation = user.cancel_follow(user_id, t['id'])

    if flag is True:
        code = RGResCode.ok
    else:
        code = RGResCode.del_fail
    return jsonify(form_res(code, None))


@RestRouter.route('/editname', methods=['POST'])
@RGUIController.auth_handler(page=False)
def user_edit_name(user_id):
    t = get_data_with_request(request)

    if 'name' in t:
        name = t['name']
        flag = user.update_name(user_id, name)
        if flag is True:
            code = RGResCode.ok
        else:
            code = RGResCode.not_existed
        return jsonify(form_res(code, None))
    else:
        return jsonify(form_res(RGResCode.lack_param, None))


@RestRouter.route('/editTitle', methods=['POST'])
@RGUIController.auth_handler(page=False)
def user_edit_title(user_id):
    t = get_data_with_request(request)
    if 'name' in t:
        name = t['name']
        flag = user.update_title(user_id, name)
        if flag is True:
            code = RGResCode.ok
        else:
            code = RGResCode.not_existed
        return jsonify(form_res(code, None))
    else:
        return jsonify(form_res(RGResCode.lack_param, None))


@RestRouter.route('/editdesc', methods=['POST'])
@RGUIController.auth_handler(page=False)
def user_edit_desc(user_id):
    t = get_data_with_request(request)

    if 'desc' in t:
        name = t['desc']
        flag = user.update_desc(user_id, name)
        if flag is True:
            code = RGResCode.ok
        else:
            code = RGResCode.not_existed
        return jsonify(form_res(code, None))
    else:
        return jsonify(form_res(RGResCode.lack_param, None))


@RestRouter.route('/setInfo', methods=['POST'])
@RGUIController.auth_handler(page=False)
def user_set_info(user_id):
    t = get_data_with_request(request)

    file_stream = {}

    re_files = request.files
    for name in re_files:
        stream = re_files[name]
        value = (stream.filename, stream.stream, stream.content_type)
        file_stream[name] = value

    url = RGFullThisServerHost + '/file/upload/'
    req = requests.post(url=url, files=file_stream, data=request.form, params=None,
                        auth=request.authorization, cookies=request.cookies, hooks=None, json=request.json, stream=True)

    res_json = req.json()
    print(res_json)

    tag = None
    nickname = None
    style = None
    bg_id = None
    icon_id = None

    if 'data' in res_json:
        data = res_json['data']
        if 'background' in data:
            bg_file = data['background']
            if bg_file['success'] is False:
                return jsonify(form_res(RGResCode.insert_fail, None))
            bg_id = bg_file['file']['ID']

        if 'icon' in data:
            icon_file = data['icon']
            if icon_file['success'] is False:
                return jsonify(form_res(RGResCode.insert_fail, None))
            icon_id = icon_file['file']['ID']

    if 'nickname' in t:
        nickname = t['nickname']

    if 'style' in t:
        style = t['style']

    if 'tag' in t:
        tag = t['tag']

    if icon_id is None:
        if 'iconId' in t:
            icon_id = t['iconId']

    if bg_id is None:
        if 'bgId' in t:
            bg_id = t['bgId']

    flag = user.update_user_info(user_id=user_id, nickname=nickname, tag=tag, icon=icon_id, background=bg_id, style=style)
    if flag is True:
        code = RGResCode.ok
    else:
        code = RGResCode.update_fail
    return jsonify(form_res(code, None))


def send_verify_mail(receiver, content, title):
    _user = RGMailConfig['user']
    _pwd = RGMailConfig['pwd']

    # "smtp.163.com" 163的SMTP服务器
    mail_host = RGMailConfig["mailHost"]

    # 第一部分：准备工作
    # 1.将邮件的信息打包成一个对象
    message = MIMEText(content, "plain", "utf-8")  # 内容，格式，编码
    # 2.设置邮件的发送者
    message["From"] = _user
    # 3.设置邮件的接收方
    message["To"] = receiver
    # join():通过字符串调用，参数为一个列表
    # message["To"] = ",".join(receiver)
    # 4.设置邮件的标题
    message["Subject"] = title

    # 第二部分：发送邮件
    # 1.启用服务器发送邮件
    # 参数：服务器，端口号
    smtpObj = smtplib.SMTP_SSL(mail_host, RGMailConfig["sendMailPort"])
    # 2.登录邮箱进行验证
    # 参数：用户名，授权码
    smtpObj.login(_user, _pwd)
    # 3.发送邮件
    # 参数：发送方，接收方，邮件信息
    smtpObj.sendmail(_user, receiver, message.as_string())
