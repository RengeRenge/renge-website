import requests
from flask import Blueprint, request, jsonify, render_template, url_for, redirect, session, json

import RGUIController
from Model import article, user, tokens, pic
from RGGlobalConfigContext import RGHost, RGFullThisServerHost
from RGUtil.RGCodeUtil import http_code
from RGUtil.RGRequestHelp import get_data_with_request, form_res

RestRouter = Blueprint('RGUser', __name__, url_prefix='/user', static_folder='../static')

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

    return render_template("friends.html", **t)


@RestRouter.route('/set', methods=["GET"])
@RGUIController.auth_handler(page=True)
def set_page(user_id):
    t = {
        "user": user.get_user(user_id, needIcon=True),
    }
    return render_template("setting.html", **t)


"""
restful
"""


@RestRouter.route('/check', methods=['GET'])
def user_check():
    t = get_data_with_request(request)
    use = user.get_user_with_name(t['username'])
    code = http_code.not_existed if use is None else http_code.ok
    return jsonify(form_res(code, use))


@RestRouter.route('/new', methods=['POST'])
def user_new():
    t = get_data_with_request(request)
    use = user.new_user(t['username'], t['pwd'])
    token_type = int(t['type'])
    if use is not None:
        token = tokens.generate_token_ifneed(use.ID, token_type)

        session['token'] = token
        session['user_id'] = use.ID
        session['user_name'] = use.username
        session['type'] = token_type

        return jsonify(form_res(http_code.ok, {
            'token': token,
            'user': json.dumps(use.__dict__)
        }))
    else:
        return jsonify(form_res(http_code.not_existed, None))


@RestRouter.route('/login', methods=['POST'])
def user_login():
    t = get_data_with_request(request)
    use = user.user_login(t['username'], t['pwd'])
    token_type = int(t['type'])
    if use is not None:
        token = tokens.generate_token_ifneed(use.ID, token_type)

        # c = requests.cookies.RequestsCookieJar()
        # c.set('cookie-token', token, path='/')
        # sessions.cookies.update(c)
        session['token'] = token
        session['user_id'] = use.ID
        session['user_name'] = use.username
        session['type'] = token_type
        session.permanent = True

        resp = jsonify(form_res(http_code.ok, {
            'token': token,
            'user': json.dumps(use.__dict__)
        }))
        return resp
    else:
        return jsonify(form_res(http_code.not_existed, None))


@RestRouter.route('/logout', methods=['POST'])
@RGUIController.auth_handler(page=False)
def user_logout(user_id):
    t = get_data_with_request(request)
    token_type = int(t['type'])

    result = tokens.destroy_token(user_id=user_id, token_type=token_type)

    if result:
        session['token'] = None
        session['user_id'] = None
        session['user_name'] = None
        session['type'] = None
        session.permanent = False

        return jsonify(form_res(http_code.ok, None))
    else:
        return jsonify(form_res(http_code.del_fail, None))


@RestRouter.route('/follow', methods=['POST'])
@RGUIController.auth_handler(page=False)
def user_follow(user_id):
    t = get_data_with_request(request)

    other_id = int(t['id'])
    flag, relation = user.follow(user_id, t['id'])

    if flag is True:
        code = http_code.ok
        data = {
            'relation': relation,
            're_relation': user.get_relation(other_id, user_id),
        }
    else:
        code = http_code.insert_fail
        data = None
    return jsonify(form_res(code, data))


@RestRouter.route('/unfollow', methods=['POST'])
@RGUIController.auth_handler(page=False)
def cancel_follow(user_id):
    t = get_data_with_request(request)

    flag, relation = user.cancel_follow(user_id, t['id'])

    if flag is True:
        code = http_code.ok
    else:
        code = http_code.del_fail
    return jsonify(form_res(code, None))


@RestRouter.route('/editname', methods=['POST'])
@RGUIController.auth_handler(page=False)
def user_edit_name(user_id):
    t = get_data_with_request(request)

    if 'name' in t:
        name = t['name']
        flag = user.update_name(user_id, name)
        if flag is True:
            code = http_code.ok
        else:
            code = http_code.not_existed
        return jsonify(form_res(code, None))
    else:
        return jsonify(form_res(http_code.lack_param, None))


@RestRouter.route('/editTitle', methods=['POST'])
@RGUIController.auth_handler(page=False)
def user_edit_title(user_id):
    t = get_data_with_request(request)
    if 'name' in t:
        name = t['name']
        flag = user.update_title(user_id, name)
        if flag is True:
            code = http_code.ok
        else:
            code = http_code.not_existed
        return jsonify(form_res(code, None))
    else:
        return jsonify(form_res(http_code.lack_param, None))


@RestRouter.route('/editdesc', methods=['POST'])
@RGUIController.auth_handler(page=False)
def user_edit_desc(user_id):
    t = get_data_with_request(request)

    if 'desc' in t:
        name = t['desc']
        flag = user.update_desc(user_id, name)
        if flag is True:
            code = http_code.ok
        else:
            code = http_code.not_existed
        return jsonify(form_res(code, None))
    else:
        return jsonify(form_res(http_code.lack_param, None))


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
                return jsonify(form_res(http_code.insert_fail, None))
            bg_id = bg_file['file']['ID']

        if 'icon' in data:
            icon_file = data['icon']
            if icon_file['success'] is False:
                return jsonify(form_res(http_code.insert_fail, None))
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

    flag = user.update_user_info(user_id, nickname=nickname, tag=tag, icon=icon_id, background=bg_id, style=style)
    if flag is True:
        code = http_code.ok
    else:
        code = http_code.update_fail
    return jsonify(form_res(code, None))
