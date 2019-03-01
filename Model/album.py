# encoding: utf-8
from DAO import rg_dao as dao
from Files.RGFileGlobalConfigContext import url_with_name
from Model import user
from RGUtil import RGTimeUtil


class album:
    def __init__(self, ID, userId, title, desc, cover, level, timestamp):
        self.ID = ID
        self.userId = userId
        self.title = title
        self.desc = desc
        self.cover = cover
        self.level = level
        self.timestamp = timestamp


def album_obj_with_result(result):
    _album = album(
        result[0],
        result[1],
        result[2],
        result[3],
        result[4],
        result[5],
        result[6],
    )
    return _album


def default_album(user_id):
    sql = "Select * from album where user_id=%(user_id)s order by id limit 1"
    result, count, new_id = dao.execute_sql(sql, args={'user_id': user_id})
    if count is 0:
        return new_album(user_id=user_id, title='默认相册', desc='默认相册', level=2)
    else:
        return album_obj_with_result(result[0])


def del_albums(user_id, ids=[]):
    ids_str = ",".join(str(i) for i in ids)

    sql = 'delete album from album, user \
    where user.id = album.user_id and user.default_album_id != album.id and album.user_id=%s and album.id in (%s)' % (
        '%(user_id)s', ids_str)

    result, count, new_id = dao.execute_sql(sql, args={'user_id': user_id})
    if count > 0:
        return True
    else:
        return False


def new_album(user_id, title='', desc='', cover=None, level=0, timestamp=None, conn=None, commit=True):
    if timestamp is None:
        timestamp = RGTimeUtil.timestamp()

    sql = new_album_sql(user_id_key='user_id', title_key='title', desc_key='desc', cover_key='cover', level_key='level',
                        timestamp_key='timestamp')
    args = {
        'desc': desc,
        'title': title,
        'user_id': user_id,
        'cover': cover,
        'level': level,
        'timestamp': timestamp
    }

    if conn:
        result, count, new_id, error = dao.do_execute_sql_with_connect(sql, neednewid=True, conn=conn, commit=commit, args=args)
    else:
        result, count, new_id, error = dao.do_execute_sql(sql, neednewid=True, commit=commit, args=args)

    if count > 0:
        return album(new_id, user_id, title, desc, cover, level, timestamp)
    else:
        return None


def new_album_sql(user_id_key, title_key, desc_key, cover_key, level_key, timestamp_key):
    return "INSERT INTO album (user_id, title, description, `level`, cover, timestamp) VALUES \
            (%({})s, %({})s, %({})s, %({})s, %({})s, %({})s)" \
        .format(user_id_key, title_key, desc_key, level_key, cover_key, timestamp_key)


def album_list(user_id, other_id):
    # type: (int, int) -> (list, int)
    user_id = int(user_id)
    other_id = int(other_id)
    relation = 0

    lastPicUrl = 'lastPicUrl'
    coverUrl = 'coverUrl'

    sql = "SELECT ab.*, covers.file_name as '{}', jp.file_name as '{}' \
                    FROM \
                    album as ab \
                    left join (select file.file_name, pic.album_id \
                        from pic, file \
                        where pic.file_id = file.id and pic.user_id = %(other_id)s \
                        order by file.timestamp desc limit 1) as jp \
                            on jp.album_id = ab.id \
                    left join (select file.file_name, pic.id \
                          from pic, file \
                          where pic.file_id = file.id and pic.user_id = %(other_id)s) as covers \
                          on covers.id = ab.cover \
                    where ab.user_id=%(other_id)s {} order by ab.id desc".format(coverUrl, lastPicUrl, '{}')

    if other_id == user_id:
        sql = sql.format('')
    else:
        relation = user.get_relation(other_id, user_id)
        if relation == 0:
            sql = sql.format('and level=0')
        elif relation == 1:
            sql = sql.format('and level<=1')
        else:
            return None, relation
    print(sql)
    result, count, new_id = dao.execute_sql(sql, needret=True, needdic=True, args={'other_id': other_id})

    if count > 0:
        for row in result:
            row[lastPicUrl] = url_with_name(row[lastPicUrl], thumb=True)
            row[coverUrl] = url_with_name(row[coverUrl], thumb=True)
        return result, relation
    else:
        return None, relation


def album_detail(album_id, relation):
    album_id = int(album_id)

    sql = "SELECT * FROM album where id=%(album_id)s {}".format('{}')

    if relation == -1:
        sql = sql.format('')
    elif relation == 0:
        sql = sql.format('and level=0')
    elif relation == 1:
        sql = sql.format('and level<=1')
    elif relation == 2:
        return False, None
    else:
        return False, None

    result, count, new_id = dao.execute_sql(sql, needdic=True, needret=True, args={'album_id': album_id})

    if result is not None and count > 0:
        return True, result[0]
    else:
        return False, None


def update_info(album_id=None, user_id=None, title=None, desc=None, cover=None, level=None):
    if album_id is None or user_id is None:
        return False

    album_id = int(album_id)

    sql = "UPDATE album SET {} where id=%(album_id)s and user_id=%(user_id)s".format('{}')

    data = []
    if title is not None:
        data.append("title=%(title)s")
    if desc is not None:
        data.append("description=%(desc)s")
    if cover is not None:
        data.append("cover=%(cover)s")
    if level is not None:
        data.append("level=%(level)s")

    if len(data) == 0:
        return False

    params = ''
    for item in data:
        if len(params) > 0:
            params += ','
        params += item

    sql = sql.format(params)
    result, count, new_id = dao.execute_sql(sql, needret=False, args={
        'user_id': user_id,
        'album_id': album_id,
        'title': title,
        'desc': desc,
        'cover': cover,
        'level': level
    })
    if count > 0:
        return True
    else:
        return False


def update_owner(album_id=None, user_id=None, conn=None, commit=True):
    sql = "UPDATE album SET user_id=%(user_id)s where id=%(album_id)s"
    args = {
        'user_id': user_id,
        'album_id': album_id,
    }
    if conn:
        result, count, new_id, error = dao.do_execute_sql_with_connect(sql=sql, conn=conn, args=args, commit=commit)
    else:
        result, count, new_id, error = dao.do_execute_sql(sql=sql, args=args, commit=commit)

    if count:
        return True
    else:
        return False
