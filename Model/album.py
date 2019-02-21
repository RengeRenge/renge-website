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
    user_id = long(user_id)
    sql = "Select * from album where user_id=%ld order by id limit 1" % user_id
    result, count, new_id = dao.execute_sql(sql)
    if count is 0:
        return new_album(user_id=user_id, title='默认相册', desc='默认相册', level=2, default=True)
    else:
        return album_obj_with_result(result[0])


def del_albums(user_id, ids=[]):

    ids_str = ",".join(str(i) for i in ids)
    sql = 'delete album from album, user \
    where user.id = album.user_id and user.default_album_id != album.id and album.user_id=%ld and album.id in (%s)' % (user_id, ids_str)

    result, count, new_id = dao.execute_sql(sql)
    if count > 0:
        return True
    else:
        return False


def new_album(user_id, title='', desc='', cover=None, level=0, default=False):
    timestamp = RGTimeUtil.timestamp()

    sql = new_album_sql(user_id=user_id, title=title, desc=desc, level=level, default=default)

    result, count, new_id = dao.execute_sql(sql, neednewid=True)

    if count > 0:
        return album(new_id, user_id, title, desc, cover, level, timestamp)
    else:
        return None


def new_album_sql(user_id, title='', desc='', level=0, default=False):
    timestamp = RGTimeUtil.timestamp()
    level = int(level)
    return "INSERT INTO album (user_id, title, description, level, timestamp) VALUES \
        (%ld, '%s', '%s', %d, %ld)" % (user_id, title, desc, level, timestamp)


def album_list(user_id, other_id):
    # type: (long, long) -> (list, int)
    user_id = long(user_id)
    other_id = long(other_id)
    relation = 0

    lastPicUrl = 'lastPicUrl'
    coverUrl = 'coverUrl'

    sql = "SELECT ab.*, covers.file_name as '%s', jp.file_name as '%s' \
                    FROM \
                    album as ab \
                    left join (select file.file_name, pic.album_id \
                        from pic, file \
                        where pic.file_id = file.id and pic.user_id = %ld \
                        order by file.timestamp desc limit 1) as jp \
                            on jp.album_id = ab.id \
                    left join (select file.file_name, pic.id \
                          from pic, file \
                          where pic.file_id = file.id and pic.user_id = %ld) as covers \
                          on covers.id = ab.cover \
                    where ab.user_id=%ld %s order by ab.id desc" \
          % (coverUrl, lastPicUrl, other_id, other_id, other_id, '%s')

    if other_id == user_id:
        sql = sql % ''
    else:
        relation = user.get_relation(other_id, user_id)
        if relation == 0:
            sql = sql % 'and level=0'
        elif relation == 1:
            sql = sql % 'and level<=1'
        else:
            return None, relation
    print sql
    result, count, new_id = dao.execute_sql(sql, needret=True, needdic=True)

    if count > 0:
        for row in result:
            row[lastPicUrl] = url_with_name(row[lastPicUrl], thumb=True)
            row[coverUrl] = url_with_name(row[coverUrl], thumb=True)
        return result, relation
    else:
        return None, relation


def album_detail(album_id, relation):
    album_id = long(album_id)

    sql = "SELECT * FROM album where id=%ld %s" % (album_id, '%s')

    if relation == -1:
        sql = sql % ''
    elif relation == 0:
        sql = sql % 'and level=0'
    elif relation == 1:
        sql = sql % 'and level<=1'
    elif relation == 2:
        return False, None
    else:
        return False, None

    result, count, new_id = dao.execute_sql(sql, needdic=True, needret=True)

    if result is not None and count > 0:
        return True, result[0]
    else:
        return False, None


def update_info(album_id=None, user_id=None, title=None, desc=None, cover=None, level=None):
    if album_id is None or user_id is None:
        return False

    album_id = long(album_id)

    sql = "UPDATE album SET %s where id=%ld and user_id=%ld" % ('%s', album_id, user_id)

    data = []
    if title is not None:
        data.append("title='%s'" % title)
    if desc is not None:
        data.append("description='%s'" % desc)
    if cover is not None:
        data.append("cover=%ld" % int(cover))
    if level is not None:
        data.append("level=%d" % int(level))

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
