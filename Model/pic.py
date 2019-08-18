import operator

from DAO import rg_dao as dao
from RGIgnoreConfig.RGFileGlobalConfigContext import url_with_name, path_with_name
from Model import album, user


class pic:
    def __init__(self, ID, albumId, url, exif_timestamp, timestamp):
        self.ID = ID
        self.albumId = albumId
        self.url = url
        self.exif_timestamp = exif_timestamp
        self.timestamp = timestamp


def new_pic(user_id, pic_file, album_id=None, title='', desc='', level=0, needFullUrl=True, original=False):
    if album_id is None:
        de_album = album.default_album(user_id)
        album_id = de_album.ID

    sql = "INSERT INTO pic (user_id, album_id, file_id, title, description, level) VALUES \
    (%(user_id)s, %(album_id)s, %(file_id)s, %(title)s, %(desc)s, %(level)s)"

    result, count, new_id = dao.execute_sql(sql, neednewid=True, args={
        'user_id': user_id,
        'album_id': album_id,
        'file_id': pic_file.ID,
        'title': title,
        'desc': desc,
        'level': level
    })

    if count is 0:
        new_id = -1
    url = url_with_name(pic_file.name, needhost=needFullUrl, original=original)
    return pic(new_id, album_id, url, pic_file.exif_timestamp, pic_file.timestamp)


def page_list(other_id, album_id, page=1, size=10, relation=0):
    # type: (int, int, int, int, int) -> (list, int, int, int, int)

    size = int(size)

    other_id = int(other_id)
    album_id = int(album_id)

    page = int(page)
    if page < 1:
        page = 1

    sql = "SELECT pic.id, pic.title, pic.description, pic.level, file.timestamp, file.exif_timestamp, file.file_name\
            FROM pic\
            left join file on pic.file_id = file.id\
          where user_id=%(other_id)s and album_id=%(album_id)s {} order by pic.id desc".format('{}')

    if relation == -1:
        sql = sql.format('')
    elif relation == 0:
        sql = sql.format('and pic.level=0')
    elif relation == 1:
        sql = sql.format('and pic.level<=1')
    else:
        return None, 0, 0, 0, 0

    result, count, new_id = dao.execute_sql(sql, needret=False, args={
        'other_id': other_id,
        'album_id': album_id
    })

    page_count = int(operator.truediv(count - 1, size)) + 1
    page = min(page, page_count)

    sql += ' limit %d offset %d' % (size, (page - 1) * size)
    print(sql)

    result, this_page_count, new_id = dao.execute_sql(sql, needdic=True, args={
        'other_id': other_id,
        'album_id': album_id
    })

    page = page if this_page_count > 0 else page_count

    for row in result:
        row['url'] = url_with_name(row['file_name'], thumb=True)
        row['qUrl'] = url_with_name(row['file_name'])

    return result, page_count, page, size, count


def id_list(user_id, album_id, current_id=1, size=1, relation=0):
    # type: (int, int, int, int, int) -> (list, int, int, int, int)

    user_id = int(user_id)
    album_id = int(album_id)
    current_id = int(current_id)

    size = int(size)
    relation = int(relation)

    if relation == -1:
        level_sql = ''
    elif relation == 0:
        level_sql = 'and pic.level=0'
    elif relation == 1:
        level_sql = 'and pic.level<=1'
    else:
        return False, [], []

    sql_format = \
        '(' + 'SELECT pic.id, pic.title, pic.description, pic.level, \
        file.id as "fileId", file.file_name as "url", \
        file.exif_timestamp as `exif_timestamp`, file.exif_lalo as `exif_lalo` \
        FROM pic left join file on pic.file_id = file.id \
        where pic.user_id=%(user_id)s and pic.album_id=%(album_id)s {} and {}  \
        {} limit {}'.format('{}', '{}', '{}', '{}') + ')'

    sql = sql_format.format(level_sql, 'pic.id < %ld' % current_id, 'order by pic.id desc', size)
    sql += 'UNION'
    sql += sql_format.format(level_sql, 'pic.id >= %ld' % current_id, 'order by pic.id', size + 1)

    print(sql)

    result, count, new_id = dao.execute_sql(sql, needdic=True, args={
        'user_id': user_id,
        'album_id': album_id
    })

    pre_id = []
    next_id = []
    for row in result:
        if row['id'] < current_id:
            next_id.append(row)
        elif row['id'] > current_id:
            pre_id.append(row)
        else:
            current = row
        row['oUrl'] = url_with_name(row['url'], original=True)
        row['qUrl'] = url_with_name(row['url'])
        row['url'] = url_with_name(row['url'], thumb=True)

    # pre_id.reverse()
    return True, pre_id, next_id, current


def update_info(p_id=None, user_id=None, title=None, desc=None, level=None):
    if p_id is None or user_id is None:
        return False

    sql = "UPDATE pic SET {} where id=%(p_id)s and user_id=%(user_id)s".format('{}')

    data = []
    if title is not None:
        data.append("title=%(title)s")
    if desc is not None:
        data.append("description=%(desc)s")
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
        'p_id': p_id,
        'user_id': user_id,
        'title': title,
        'desc': desc,
        'level': level
    })
    if count > 0:
        return True
    else:
        return False


def delete(user_id, p_id):
    sql = 'delete from pic where id=%(p_id)s and user_id=%(user_id)s'
    dao.execute_sql(sql, args={
        'user_id': user_id,
        'p_id': p_id,
    })


def info(p_id=None, user_id=None):
    if p_id is None or user_id is None:
        return False, None

    sql = "select * from pic where id=%(p_id)s and user_id=%(user_id)s"
    result, count, new_id = dao.execute_sql(sql, needdic=True, args={
        'p_id': p_id,
        'user_id': user_id
    })
    if count > 0:
        return True, result[0]
    else:
        return False, None
