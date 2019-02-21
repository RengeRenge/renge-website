# encoding: utf-8
import hashlib
import operator

import pymysql
from flask import json

from DAO import rg_dao as dao
from Files.RGFileGlobalConfigContext import url_with_name
from Model import files
from RGUtil import RGTimeUtil


class user:
    def __init__(self, ID, username, pwd, nickname, title, desc, icon, bgImage, style, tag, defaultAlbumId, addTime):
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


def user_with_dbResult(result=None, needpwd=False, needusername=False, needIcon=False, iconName=None, needBg=True,
                       bgName=None):
    if needIcon:
        icon = files.file_name(result[6], needUrl=True) if iconName is None else url_with_name(iconName)
    else:
        icon = None

    if needBg:
        bg = files.file_name(result[7], needUrl=True) if bgName is None else url_with_name(bgName)
    else:
        bg = None

    my_user = user(result[0],
                   result[1] if needusername else None,
                   result[2] if needpwd else None,
                   result[3],
                   result[4],
                   result[5],
                   icon,
                   bg,
                   result[8],
                   result[9],
                   result[10],
                   result[11],
                   )
    my_user.iconId = result[6]
    my_user.bgId = result[7]
    return my_user


def new_user(username, pwd, title='Title', desc='Desc', nick='Nickname'):
    timestamp = RGTimeUtil.timestamp()
    pwd = md5_key(pwd)

    conn = dao.get()
    cursor = conn.cursor()

    _user = None

    try:
        sql = "SELECT auto_increment\
                                FROM  information_schema.`TABLES`\
                                WHERE TABLE_SCHEMA='rg_database'AND TABLE_NAME='user'"
        cursor.execute(sql)
        new_user_id = cursor.fetchone()[0]

        import album
        sql = album.new_album_sql(user_id=new_user_id, title='日志相册', desc='默认相册', level=4)
        count = cursor.execute(sql)

        if count == 0:
            raise Exception

        cursor.execute('SELECT LAST_INSERT_ID();')
        result = cursor.fetchone()
        new_album_id = result[0]

        sql = "INSERT INTO user (username, pwd, addtime, title, description, nickname, default_album_id) VALUES \
        ('%s', '%s', %ld, '%s', '%s', '%s', %ld)" % (
            dao.escape_string(username),
            dao.escape_string(pwd),
            timestamp,
            dao.escape_string(title),
            dao.escape_string(desc),
            dao.escape_string(nick),
            new_album_id
        )

        count = cursor.execute(sql)

        if count == 0:
            raise Exception

        conn.commit()
        return get_user_with_name(username)
    except:
        conn.rollback()
        conn.commit()
    finally:
        cursor.close()


def get_user(user_id, needIcon=False, needBg=True):
    user_id = long(user_id)

    bgindex = -1
    if needIcon and needBg:
        sql = "SELECT user.*, bgFIle.file_name as 'bg', icFile.file_name as 'icon' \
              FROM user \
              left join file icFile on icFile.id = user.icon \
              left join file bgFIle on bgFIle.id = user.bg_image \
              where user.id=%ld" % user_id
        bgindex = -2
    elif needIcon:
        sql = "SELECT user.*, file.file_name as 'icon' FROM user \
        left join file on file.id = user.icon where user.id=%d" % user_id
    elif needBg:
        sql = "SELECT user.*, file.file_name as 'bg' FROM user \
        left join file on file.id = user.bg_image where user.id=%d" % user_id
    else:
        sql = "SELECT * FROM user where id=%d" % user_id

    result, count, new_id = dao.execute_sql(sql)

    if count:
        result = result[0]
        use = user_with_dbResult(result, needIcon=needIcon, iconName=result[-1], needBg=needBg, bgName=result[bgindex])
        return use
    else:
        return None


def get_user_iconname(user_id):
    user_id = long(user_id)
    sql = "SELECT file.file_name FROM user \
        left join file on file.id = user.icon where user.id=%d" % user_id

    result, count, new_id = dao.execute_sql(sql)

    if count:
        result = result[0]
        return result
    else:
        return None


def get_user_with_name(username):
    sql = "SELECT * FROM user where username='%s'" % username
    print sql

    result, count, new_id = dao.execute_sql(sql, needret=True)

    if count > 0:
        result = result[0]
        use = user_with_dbResult(result)
        return use
    else:
        return None


def md5_key(arg):
    _hash = hashlib.md5()
    _hash.update(arg)
    return _hash.hexdigest()


def user_login(username, pwd):
    pwd = md5_key(str(pwd))

    sql = "SELECT * FROM user where username='%s' AND pwd='%s'" % (str(username), pwd)
    print (sql)

    result, count, new_id = dao.execute_sql(sql)

    if count > 0:
        result = result[0]
        use = user_with_dbResult(result)
        return use
    else:
        return None


def follow(my_id, other_id):
    return change_relation(my_id, other_id, 1)


def cancel_follow(my_id, other_id):
    return change_relation(my_id, other_id, 0)


def block(my_id, other_id):
    return change_relation(my_id, other_id, 2)


def change_relation(my_id, other_id, relation=0):
    timestamp = RGTimeUtil.timestamp()

    my_id = long(my_id)
    other_id = long(other_id)

    sql = "INSERT INTO user_relation (m_user_id, o_user_id, relation, addtime) \
        VALUES (%ld, %ld, %d, %ld) ON DUPLICATE KEY UPDATE relation=%d, addtime=%ld" \
          % (my_id, other_id, relation, timestamp, relation, timestamp)
    print (sql)

    result, count, new_id = dao.execute_sql(sql, needret=False)

    if count > 0:
        return True, relation
    else:
        return False, relation


def get_relation(my_id, other_id):
    # type: (long, long) -> int
    my_id = long(my_id)
    other_id = long(other_id)
    if my_id == other_id:
        return -1
    sql = "SELECT * FROM user_relation where m_user_id =%ld AND o_user_id=%ld" % (my_id, other_id)
    result, count, new_id = dao.execute_sql(sql, needdic=True)
    if count > 0:
        return result[0]['relation']
    else:
        return 0


def update_name(user_id, name):
    user_id = long(user_id)
    sql = "UPDATE user SET nickname = '%s' where id=%ld" % (dao.escape_string(name), user_id)
    result, count, new_id = dao.execute_sql(sql, needret=False)
    if count > 0:
        return True
    else:
        return False


def update_title(user_id, title):
    user_id = long(user_id)
    title = dao.escape_string(title)
    sql = "UPDATE user SET title = '%s' where id=%ld" % (dao.escape_string(title), user_id)
    result, count, new_id = dao.execute_sql(sql, needret=False)
    if count > 0:
        return True
    else:
        return False


def update_desc(user_id, desc):
    user_id = long(user_id)
    sql = "UPDATE user SET description = '%s' where id=%ld" % (dao.escape_string(desc), user_id)
    result, count, new_id = dao.execute_sql(sql, needret=False)
    if count > 0:
        return True
    else:
        return False


def update_user_info(user_id, nickname=None, icon=None, background=None, tag=None, style=None):
    user_id = long(user_id)

    sql = "UPDATE user SET %s where id=%ld" % ('%s', user_id)

    data = []
    if nickname:
        nickname = dao.escape_string(nickname)
        data.append("nickname='%s'" % nickname)
    if icon:
        icon = long(icon)
        data.append("icon=%ld" % icon)
    if background:
        background = long(background)
        data.append("bg_image=%ld" % background)
    if tag:
        tag = dao.escape_string(tag)
        data.append("tag='%s'" % tag)
    if style:
        data.append("style='%s'" % style)

    if len(data) == 0:
        return False

    params = ''
    for item in data:
        if len(params) > 0:
            params += ','
        params += item

    sql = sql % params
    result, count, new_id = dao.execute_sql(sql % data, needret=False)
    if count > 0:
        return True
    else:
        return False


def friend_page_list(user_id, page=1, size=10):
    user_id = long(user_id)
    size = int(size)
    page = int(page)
    if page < 1:
        page = 1

    sql_temp = "SELECT %s FROM user_relation as re, user as u %s \
    where re.relation=1 and re.m_user_id=%ld and re.o_user_id = u.id \
    order by %s DESC " \
               % ('%s', '%s', user_id, '%s')

    sql = sql_temp % ('count(*)', '', 're.addtime')
    print sql
    result, count, new_id = dao.execute_sql(sql, needret=True)

    if count > 0:
        count = result[0][0]
    page_count = int(operator.truediv(count - 1, size)) + 1
    page = min(page, page_count)

    sql = sql_temp % ("re.addtime as 'follow_time', file.file_name as icon,\
    u.nickname, u.tag, u.id as 'ID', u.description as 'desc', u.addtime as 'addTime'"
                      , ' left join file on file.id = u.icon'
                      , 'follow_time')

    offset = (size, (page - 1) * size)
    sql += (' limit %d offset %d' % offset)
    print sql

    result, this_page_count, new_id = dao.execute_sql(sql, needdic=True)

    page = page if this_page_count > 0 else page_count

    for row in result:
        icon = row['icon']
        if icon is not None and len(icon):
            row['icon'] = url_with_name(icon)

    return result, page_count, page, size, count


def icon_url(user_id):
    get_user(user_id)
    files.file_name()
