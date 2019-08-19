# encoding: utf-8
import hashlib
import operator
import random

from flask import json

import User
from DAO import rg_dao as dao
from Model import files
from RGIgnoreConfig.RGFileGlobalConfigContext import url_with_name
from RGUtil import RGTimeUtil
from RGUtil.RGCodeUtil import RGResCode, RGVerifyType
from User import RGOpenIdController

salt = 'Renge'


class user:
    def __init__(self, ID, username, pwd, nickname, title, desc, icon, bgImage, style, tag, defaultAlbumId, addTime,
                 info_payload, is_active, is_delete, email):
        self.ID = ID
        self.username = username
        self.pwd = pwd
        self.nickname = nickname
        self.title = title
        self.desc = desc
        self.icon = icon
        self.bgImage = '' if bgImage is None else bgImage
        self.style = json.loads('{}' if style is None else style)
        self.tag = '' if tag is None else tag
        self.defaultAlbumId = defaultAlbumId
        self.addTime = addTime
        self.infoPayload = info_payload
        self.isActive = is_active
        self.isDelete = is_delete
        self.email = email

    def get_payload(self, key=None, default=None):
        if self.infoPayload is None:
            payload = {}
        else:
            try:
                payload = json.loads(self.infoPayload)
            except:
                payload = {}
        if key is None:
            return payload
        else:
            return payload[key] if key in payload else default

    def is_full_active(self):
        return True if (self.isActive == 1 and self.has_email()) else False

    def is_active_and_need_bind_email(self):
        """
        判断是没有接入OpenID的老用户
        :return: True or False
        """
        if self.has_email():
            return False
        code, _users = User.RGOpenIdController.user_list(username=self.username)
        if code == RGResCode.ok and len(_users) > 0:
            open_id_exist = True
        else:
            open_id_exist = False
        return True if (self.isActive == 1 and not open_id_exist) else False

    def is_time_out(self, check_time=None):
        _type = self.get_payload(key='type', default=None)
        if _type is None:
            return True
        if _type != RGVerifyType.forget_pwd and self.is_full_active():
            return True
        return user_is_timeout(add_time=self.get_payload(key='timestamp', default=0), check_time=check_time)

    def has_email(self):
        return True if self.email is not None and len(self.email) > 0 else False

    def is_allow_resend_email(self, now_time=None):
        _type = self.get_payload(key='type', default=None)
        if _type is None:
            return True

        if _type != RGVerifyType.forget_pwd and self.is_full_active():
            return False
        if now_time is None:
            now_time = RGTimeUtil.timestamp()
        if now_time > self.get_payload(key='timestamp', default=0) + 5 * 60 * 1000:
            return True
        return False

    def verify_code(self, code, email, v_type):
        _type = int(v_type)

        if _type != int(self.get_payload(key='type')):
            return False
        elif _type == RGVerifyType.new:
            if self.is_full_active():
                return False
        elif _type == RGVerifyType.bind:
            if self.isActive == 0 or self.has_email():
                return False
        elif _type == RGVerifyType.forget_pwd:
            pass
        else:
            return False

        save_code = int(self.get_payload(key='code'))

        if save_code == code: #and email == self.get_payload(key='email'):
            return True
        else:
            return False


def generate_verify_code():
    code = random.randint(100000, 999999)
    return code


def user_is_timeout(add_time, check_time=None):
    if check_time is None:
        check_time = RGTimeUtil.timestamp()
    if add_time + 10 * 60 * 1000 < check_time:
        return True
    return False


def user_with_db_result(result=None, need_pwd=False, need_username=False, need_icon=False, icon_name=None, need_bg=False,
                        bg_name=None, need_email=False):
    if need_icon:
        icon = files.file_name(result[6], needUrl=True) if icon_name is None else url_with_name(icon_name, thumb=True)
    else:
        icon = None

    if need_bg:
        bg = files.file_name(result[7], needUrl=True) if bg_name is None else url_with_name(bg_name, original=True)
    else:
        bg = None

    username = result[1]
    if need_email:
        data = User.RGOpenIdController.user_data(username=username)
        email = data['email'] if (data is not None and 'email' in data) else None
    else:
        email = None

    my_user = user(result[0],
                   username if need_username else None,
                   result[2] if need_pwd else None,
                   result[3],
                   result[4],
                   result[5],
                   icon,
                   bg,
                   result[8],
                   result[9],
                   result[10],
                   result[11],
                   result[12],
                   result[13],
                   result[14],
                   email
                   )
    my_user.iconId = result[6]
    my_user.bgId = result[7]
    return my_user


def login_sign_check(username):
    sql = "SELECT * FROM user where username=%(username)s"
    result, count, new_id = dao.execute_sql(sql, needret=True, args={'username': username})

    _user = None
    if count > 0:
        _user = user_with_db_result(result[0])
    return _user


def new_user_and_save_verify_code(username, email, verify_code, verify_type=RGVerifyType.new):

    if username is None or email is None:
        return RGResCode.lack_param
    if len(username) <= 0 or len(email) <= 0:
        return RGResCode.lack_param

    timestamp = RGTimeUtil.timestamp()

    conn = None
    res_code = RGResCode.server_error
    try:
        conn = dao.get()

        # OPEN ID
        res_code, data = User.RGOpenIdController.user_list(email=email)
        if res_code != RGResCode.ok:
            raise Exception

        if verify_type == RGVerifyType.forget_pwd:
            if data is not None and len(data) > 0:
                if data[0]['username'] != username:
                    res_code = RGResCode.auth_fail
                    raise Exception
            else:
                res_code = RGResCode.not_existed
                raise Exception
        else:
            if data is not None and len(data) > 0:
                res_code = RGResCode.has_existed
                raise Exception

        # OPEN ID
        if verify_code == RGVerifyType.bind and verify_code == RGVerifyType.new:
            res_code, data = User.RGOpenIdController.user_list(username=username)
            if res_code != RGResCode.ok:
                raise Exception
            if data is not None and len(data) > 0:
                res_code = RGResCode.has_existed
                raise Exception

        sql = "SELECT * FROM user where username=%(username)s"
        result, count, new_id, err = dao.do_execute_sql_with_connect(
            sql=sql,
            needret=True,
            commit=False,
            conn=conn,
            args={'username': username}
        )
        if err:
            res_code = RGResCode.server_error
            raise Exception
        if count > 0:
            _user = user_with_db_result(result[0], need_email=True)
            if verify_type == RGVerifyType.new:
                if _user.is_full_active() or _user.has_email():
                    res_code = RGResCode.user_has_existed
                    raise Exception
            elif verify_type == RGVerifyType.bind:
                if _user.has_email():
                    res_code = RGResCode.user_has_existed
                    raise Exception
            elif verify_type == RGVerifyType.forget_pwd:
                pass
            else:
                res_code = RGResCode.lack_param
                raise Exception

            if _user.is_allow_resend_email(now_time=timestamp) is False:
                res_code = RGResCode.frequent
                raise Exception

        sql = "INSERT INTO user (username, addtime, pwd, is_active, info_payload) VALUES \
            (%(username)s, %(timestamp)s, %(pwd)s, %(is_active)s, %(info_payload)s) \
            ON DUPLICATE KEY UPDATE info_payload=%(info_payload)s"

        payload = json.dumps({
            'code': verify_code,
            'email': email,
            'type': verify_type,
            'timestamp': RGTimeUtil.timestamp()
        })
        args = {
            'username': username,
            'timestamp': timestamp,
            'pwd': '',
            'is_active': 0,
            'info_payload': payload
        }

        result, count, new_id, err = dao.do_execute_sql_with_connect(
            sql=sql,
            args=args,
            conn=conn,
            commit=False
        )

        if err:
            res_code = RGResCode.server_error
            raise Exception

        conn.commit()
        return res_code
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()
        return res_code
    finally:
        dao.close(conn, None)


def verify_user(username, email, pwd, verify_code, verify_type, title='Title', desc='Desc', nick='Nickname'):
    check_time = RGTimeUtil.timestamp()
    res_code = RGResCode.server_error

    conn = None
    try:
        conn = dao.get()
        sql = "SELECT * FROM user where username=%(username)s"
        result, count, new_id, err = dao.do_execute_sql_with_connect(
            sql=sql,
            needret=True,
            commit=False,
            conn=conn,
            args={'username': username}
        )

        if err:
            res_code = RGResCode.server_error
            raise Exception

        if count <= 0:
            res_code = RGResCode.not_existed
            raise Exception

        _user = user_with_db_result(result[0], need_pwd=True, need_email=True)
        if verify_type != RGVerifyType.forget_pwd and _user.is_full_active():
            res_code = RGResCode.has_existed
            raise Exception

        # 超时
        if _user.is_time_out(check_time=check_time):
            res_code = RGResCode.timeout
            raise Exception

        # 校验验证码
        if verify_type == RGVerifyType.new or verify_type == RGVerifyType.forget_pwd:
            email = _user.get_payload(key='email')
        if not _user.verify_code(code=verify_code, email=email, v_type=verify_type):
            res_code = RGResCode.verify_code_incorrect
            raise Exception

        # 创建默认相册
        user_id = _user.ID
        if verify_type == RGVerifyType.new:
            from Model import album
            _album = album.new_album(user_id=user_id, title='日志相册', desc='默认相册', cover=None,
                                     level=2, timestamp=check_time, conn=conn, commit=False)

            if _album is None:
                res_code = RGResCode.server_error
                raise Exception
            new_album_id = _album.ID
            _user.addTime = check_time
        else:
            new_album_id = _user.defaultAlbumId

        sha256_pwd = sha256_key(username, pwd)

        args = {
            'pwd': sha256_pwd,
            'add_time': _user.addTime,
            'title': title,
            'desc': desc,
            'nick': nick,
            'new_album_id': new_album_id,
            'id': user_id,
            'is_active': 1,
            'info_payload': ''
        }

        if verify_type == RGVerifyType.new:
            sql = "UPDATE user SET " \
                  "pwd=%(pwd)s, " \
                  "addtime=%(add_time)s, " \
                  "title=%(title)s, " \
                  "description=%(desc)s, " \
                  "nickname=%(nick)s, " \
                  "default_album_id=%(new_album_id)s, " \
                  "is_active=%(is_active)s, " \
                  "info_payload=%(info_payload)s " \
                  "where id=%(id)s"
        elif verify_type == RGVerifyType.bind:
            if sha256_pwd != _user.pwd:
                res_code = RGResCode.password_incorrect
                raise Exception
            sql = "UPDATE user SET " \
                  "info_payload=%(info_payload)s " \
                  "where id=%(id)s"
        elif verify_type == RGVerifyType.forget_pwd:
            sql = "UPDATE user SET " \
                  "pwd=%(pwd)s, " \
                  "info_payload=%(info_payload)s " \
                  "where id=%(id)s"

        result, count, new_id, err = dao.do_execute_sql_with_connect(
            sql=sql,
            args=args,
            conn=conn,
            commit=False,
            needret=True,
        )

        if err:
            res_code = RGResCode.server_error
            raise Exception

        if verify_type == RGVerifyType.new:
            code = RGOpenIdController.user_new(username=username, email=email, password=pwd)
        elif verify_type == RGVerifyType.bind:
            code = RGOpenIdController.user_new(username=username, email=email, password=pwd)
        elif verify_type == RGVerifyType.forget_pwd:
            code = RGOpenIdController.user_update(username=username, password=pwd)
        else:
            code = RGResCode.lack_param

        if code != RGResCode.ok:
            res_code = code
            raise Exception

        res_code = RGResCode.ok
        conn.commit()
        return _user.ID, res_code
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()
        return None, res_code
    finally:
        dao.close(conn, None)


def new_user(username, pwd, title='Title', desc='Desc', nick='Nickname'):
    timestamp = RGTimeUtil.timestamp()
    pwd = sha256_key(username, pwd)

    _user = None

    conn = None
    cursor = None
    try:
        conn = dao.get()
        cursor = conn.cursor()
        # 某些时候获取到重复的ID
        # sql = "SELECT auto_increment FROM  information_schema.`TABLES` \
        #         WHERE TABLE_SCHEMA='rg_database'AND TABLE_NAME='user'"
        # cursor.execute(sql)
        new_user_id = -1

        from Model import album
        _album = album.new_album(user_id=new_user_id, title='日志相册', desc='默认相册', cover=None,
                                 level=2, timestamp=timestamp, conn=conn, commit=False)

        if _album is None:
            raise Exception

        new_album_id = _album.ID

        sql = "INSERT INTO user (username, pwd, addtime, title, description, nickname, default_album_id) VALUES \
        (%(username)s, %(pwd)s, %(timestamp)s, %(title)s, %(desc)s, %(nick)s, %(new_album_id)s)"

        count = cursor.execute(sql, args={
            'username': username,
            'pwd': pwd,
            'timestamp': timestamp,
            'title': title,
            'desc': desc,
            'nick': nick,
            'new_album_id': new_album_id,
            'is_active': 1
        })

        if count == 0:
            raise Exception

        new_user_id = dao.get_last_insert(cursor=cursor)[0]
        flag = album.update_owner(album_id=new_album_id, user_id=new_user_id, conn=conn, commit=False)
        if not flag:
            raise Exception

        conn.commit()
        return get_user_with_username(username, need_email=True)
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()
        return None
    finally:
        dao.close(conn, cursor)


def user_login(username, pwd):
    sql = "SELECT * FROM user where username=%(username)s"
    result, count, new_id = dao.execute_sql(sql=sql, args={'username': username})

    _user = None

    if count <= 0:
        code, data = User.RGOpenIdController.auth(username=username, password=pwd)
        if code == RGResCode.ok and data is not None and len(data) > 0:
            _user = new_user(username=username, pwd=pwd)
    else:
        _user = user_with_db_result(result[0], need_pwd=True, need_username=True, need_email=True)
        if _user.is_active_and_need_bind_email():
            if _user.pwd != sha256_key(username, pwd):
                _user = None
        else:
            code, data = User.RGOpenIdController.auth(username=username, password=pwd)
            if code == RGResCode.ok and data is not None and len(data) > 0:
                pass
            else:
                _user = None
    return _user


def get_user_with_username(username, need_email=True):
    sql = "SELECT * FROM user where username=%(username)s"

    result, count, new_id = dao.execute_sql(sql, args={
        'username': username
    })

    if count > 0:
        return user_with_db_result(result[0], need_pwd=True, need_username=True, need_email=need_email)
    else:
        return None


def get_user(user_id, need_icon=False, need_bg=True, need_email=False, need_username=False):
    user_id = int(user_id)

    bgindex = -1
    if need_icon and need_bg:
        sql = "SELECT user.*, bgFIle.file_name as 'bg', icFile.file_name as 'icon' \
              FROM user \
              left join file icFile on icFile.id = user.icon \
              left join file bgFIle on bgFIle.id = user.bg_image \
              where user.id=%(user_id)s"
        bgindex = -2
    elif need_icon:
        sql = "SELECT user.*, file.file_name as 'icon' FROM user \
        left join file on file.id = user.icon where user.id=%(user_id)s"
    elif need_bg:
        sql = "SELECT user.*, file.file_name as 'bg' FROM user \
        left join file on file.id = user.bg_image where user.id=%(user_id)s"
    else:
        sql = "SELECT * FROM user where id=%(user_id)s"

    result, count, new_id = dao.execute_sql(sql, args={
        'user_id': user_id
    })

    if count:
        result = result[0]
        _user = user_with_db_result(result, need_icon=need_icon, icon_name=result[-1], need_bg=need_bg, bg_name=result[bgindex], need_email=need_email, need_username=need_username)
        return _user
    else:
        return None


def get_user_icon_name(user_id):
    sql = """SELECT file.file_name FROM user
        left join file on file.id = user.icon where user.id=%(user_id)s"""

    result, count, new_id = dao.execute_sql(sql, args={'user_id': user_id})

    if count:
        result = result[0]
        return result
    else:
        return None


def sha256_key(username, pwd):
    _hash = hashlib.md5()
    _hash.update(pwd.encode("utf8"))
    pwd = _hash.hexdigest()

    pwd = username + salt + pwd

    _hash = hashlib.sha256()
    _hash.update(pwd.encode("utf8"))
    pwd = _hash.hexdigest()

    return pwd


def follow(my_id, other_id):
    return change_relation(my_id, other_id, 1)


def cancel_follow(my_id, other_id):
    return change_relation(my_id, other_id, 0)


def block(my_id, other_id):
    return change_relation(my_id, other_id, 2)


def change_relation(my_id, other_id, relation=0):
    timestamp = RGTimeUtil.timestamp()

    sql = """INSERT INTO user_relation (m_user_id, o_user_id, relation, addtime)
        VALUES (%(my_id)s, %(other_id)s, %(relation)s, %(timestamp)s) 
        ON DUPLICATE KEY UPDATE relation=%(relation)s, addtime=%(timestamp)s"""

    result, count, new_id = dao.execute_sql(sql=sql,
                                            needret=False,
                                            args={'my_id': my_id,
                                                  'other_id': other_id,
                                                  'relation': relation,
                                                  'timestamp': timestamp
                                                  }
                                            )

    if count > 0:
        return True, relation
    else:
        return False, relation


def get_relation(my_id, other_id):
    # type: (int, int) -> int
    if my_id is None or other_id is None:
        return 0

    my_id = int(my_id)
    other_id = int(other_id)
    if my_id == other_id:
        return -1
    sql = "SELECT * FROM user_relation where m_user_id =%(my_id)s AND o_user_id=%(other_id)s"
    result, count, new_id = dao.execute_sql(sql, needdic=True, args={'my_id': my_id, 'other_id': other_id})
    if count > 0:
        return result[0]['relation']
    else:
        return 0


def isHome(my_id, other_id):
    if my_id is None or other_id is None:
        return False
    return int(my_id) == int(other_id)


def update_name(user_id, name):
    sql = "UPDATE user SET nickname = %(name)s where id=%(user_id)s"
    result, count, new_id = dao.execute_sql(sql, needret=False, args={'name': name, 'id': user_id})
    if count > 0:
        return True
    else:
        return False


def update_title(user_id, title):
    sql = "UPDATE user SET title = %(title)s where id=%(user_id)s"
    result, count, new_id = dao.execute_sql(sql, needret=False, args={'title': title, 'user_id': user_id})
    if count > 0:
        return True
    else:
        return False


def update_desc(user_id, desc):
    sql = "UPDATE user SET description = %(desc)s where id=%(user_id)s"
    result, count, new_id = dao.execute_sql(sql, needret=False, args={'desc': desc, 'user_id': user_id})
    if count > 0:
        return True
    else:
        return False


def update_user_info(user_id=None, username=None,
                     nickname=None, icon=None, background=None, tag=None, style=None, info_payload=None):
    if user_id is None and username is None:
        return False
    data = []
    if nickname is not None:
        data.append("nickname=%(nickname)s")
    if icon is not None:
        data.append("icon=%(icon)s")
    if background is not None:
        data.append("bg_image=%(background)s")
    if tag is not None:
        data.append("tag=%(tag)s")
    if style is not None:
        data.append("style=%(style)s")
    if info_payload is not None:
        data.append("info_payload=%(info_payload)s")

    if len(data) == 0:
        return False

    params = ''
    for item in data:
        if len(params) > 0:
            params += ','
        params += item

    if user_id is not None:
        sql = "UPDATE user SET {} where id=%(user_id)s".format(params)
    else:
        sql = "UPDATE user SET {} where username=%(username)s".format(params)

    args = {
        'nickname': nickname,
        'icon': icon,
        'background': background,
        'tag': tag,
        'style': style,
        'info_payload': info_payload,
        'user_id': user_id,
        'username': username
    }
    result, count, new_id, error = dao.execute_sql_err(sql, needret=False, args=args)
    return True if error is None else False


def friend_page_list(user_id, page=1, size=10):
    user_id = int(user_id)
    size = int(size)
    page = int(page)
    if page < 1:
        page = 1

    sql_temp = "SELECT %s FROM user_relation as re, user as u %s \
    where re.relation=1 and re.m_user_id=%s and re.o_user_id = u.id \
    order by %s DESC" % ('%s', '%s', '%s', '%s')

    sql = sql_temp % ('count(*)', '', '%(user_id)s', 're.addtime')
    print(sql)
    result, count, new_id = dao.execute_sql(sql, needret=True, args={
        'user_id': user_id,
    })

    if count > 0:
        count = result[0][0]
    page_count = int(operator.truediv(count - 1, size)) + 1
    page = min(page, page_count)

    sql = sql_temp % (
        "re.addtime as 'follow_time', file.file_name as 'icon', \
        u.nickname, u.tag, u.id as 'ID', u.title as 'title', u.description as 'desc', u.addtime as 'addTime'",
        ' left join file on file.id = u.icon',
        '%(user_id)s',
        'follow_time'
    )

    offset = (size, (page - 1) * size)
    sql += (' limit %d offset %d' % offset)
    print(sql)

    result, this_page_count, new_id = dao.execute_sql(sql, needdic=True, args={
        'user_id': user_id,
    })

    page = page if this_page_count > 0 else page_count

    for row in result:
        icon = row['icon']
        if icon is not None and len(icon):
            row['icon'] = url_with_name(icon, thumb=True)

    return result, page_count, page, size, count


def icon_url(user_id):
    get_user(user_id)
    files.file_name()
