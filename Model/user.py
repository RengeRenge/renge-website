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
        icon = files.file_name(result[6], needUrl=True) if iconName is None else url_with_name(iconName, thumb=True)
    else:
        icon = None

    if needBg:
        bg = files.file_name(result[7], needUrl=True) if bgName is None else url_with_name(bgName, original=True)
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
                                 level=2, timestamp=timestamp, commit=False)

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
            'new_album_id': new_album_id
        })

        if count == 0:
            raise Exception

        cursor.execute('SELECT LAST_INSERT_ID();')
        new_user_id = cursor.fetchone()[0]
        album.update_owner(album_id=new_album_id, user_id=new_user_id, commit=False)

        conn.commit()
        return get_user_with_name(username)
    except:
        conn.rollback()
        conn.commit()
    finally:
        dao.close(conn, cursor)


def get_user(user_id, needIcon=False, needBg=True):
    user_id = int(user_id)

    bgindex = -1
    if needIcon and needBg:
        sql = "SELECT user.*, bgFIle.file_name as 'bg', icFile.file_name as 'icon' \
              FROM user \
              left join file icFile on icFile.id = user.icon \
              left join file bgFIle on bgFIle.id = user.bg_image \
              where user.id=%(user_id)s"
        bgindex = -2
    elif needIcon:
        sql = "SELECT user.*, file.file_name as 'icon' FROM user \
        left join file on file.id = user.icon where user.id=%(user_id)s"
    elif needBg:
        sql = "SELECT user.*, file.file_name as 'bg' FROM user \
        left join file on file.id = user.bg_image where user.id=%(user_id)s"
    else:
        sql = "SELECT * FROM user where id=%(user_id)s"

    result, count, new_id = dao.execute_sql(sql, args={
        'user_id': user_id
    })

    if count:
        result = result[0]
        use = user_with_dbResult(result, needIcon=needIcon, iconName=result[-1], needBg=needBg, bgName=result[bgindex])
        return use
    else:
        return None


def get_user_iconname(user_id):
    sql = """SELECT file.file_name FROM user
        left join file on file.id = user.icon where user.id=%(user_id)s"""

    result, count, new_id = dao.execute_sql(sql, args={'user_id': user_id})

    if count:
        result = result[0]
        return result
    else:
        return None


def get_user_with_name(username):
    sql = "SELECT * FROM user where username=%(username)s"
    result, count, new_id = dao.execute_sql(sql, needret=True, args={'username': username})

    if count > 0:
        result = result[0]
        use = user_with_dbResult(result)
        return use
    else:
        return None


def md5_key(arg):
    _hash = hashlib.md5()
    _hash.update(arg.encode("utf8"))
    return _hash.hexdigest()


def user_login(username, pwd):
    pwd = md5_key(pwd)
    sql = "SELECT * FROM user where username=%(username)s AND pwd=%(pwd)s"
    result, count, new_id = dao.execute_sql(sql=sql, args={'username': username, 'pwd': pwd})

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


def update_user_info(user_id, nickname=None, icon=None, background=None, tag=None, style=None):
    data = []
    if nickname:
        data.append("nickname=%(nickname)s")
    if icon:
        data.append("icon=%(icon)s")
    if background:
        data.append("bg_image=%(background)s")
    if tag:
        data.append("tag=%(tag)s")
    if style:
        data.append("style=%(style)s")

    if len(data) == 0:
        return False

    params = ''
    for item in data:
        if len(params) > 0:
            params += ','
        params += item

    sql = "UPDATE user SET {} where id=%(user_id)s".format(params)
    args = {
        'nickname': nickname,
        'icon': icon,
        'background': background,
        'tag': tag,
        'style': style,
        'user_id': user_id
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
        u.nickname, u.tag, u.id as 'ID', u.description as 'desc', u.addtime as 'addTime'",
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
            row['icon'] = url_with_name(icon)

    return result, page_count, page, size, count


def icon_url(user_id):
    get_user(user_id)
    files.file_name()
