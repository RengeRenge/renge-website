import operator

from DAO import rg_dao as dao
from Files.RGFileGlobalConfigContext import url_with_name, path_with_name
from Model import album, user


class pic:
    def __init__(self, ID, albumId, url, exif_timestamp, timestamp):
        self.ID = ID
        self.albumId = albumId
        self.url = url
        self.exif_timestamp = exif_timestamp
        self.timestamp = timestamp


def new_pic(user_id, pic_file, album_id=None, title='', desc='', level=0, needFullUrl=True):
    if album_id is None:
        de_album = album.default_album(user_id)
        album_id = de_album.ID

    sql = "INSERT INTO pic (user_id, album_id, file_id, title, description, level) VALUES \
    (%ld, %ld, %ld, '%s', '%s', %d)" % \
          (user_id, album_id, pic_file.ID, title, desc, level)

    result, count, new_id = dao.execute_sql(sql, neednewid=True)

    if count is 0:
        new_id = -1
    url = url_with_name(pic_file.name) if needFullUrl else '/' + path_with_name(pic_file.name)
    return pic(new_id, album_id, url, pic_file.exif_timestamp, pic_file.timestamp)


def page_list(other_id, album_id, page=1, size=10, relation=0):
    # type: (long, long, int, int, int) -> (list, int, int, int, int)

    size = int(size)

    other_id = int(other_id)
    album_id = int(album_id)

    page = int(page)
    if page < 1:
        page = 1

    sql = "SELECT pic.id, pic.title, pic.description, pic.level, file.timestamp, file.exif_timestamp, file.file_name\
            FROM pic\
            left join file on pic.file_id = file.id\
          where user_id=%ld and album_id=%ld %s order by pic.id desc" % (other_id, album_id, '%s')

    if relation == -1:
        sql = sql % ''
    elif relation == 0:
        sql = sql % 'and pic.level=0'
    elif relation == 1:
        sql = sql % 'and pic.level<=1'
    else:
        return None, 0, 0, 0, 0

    result, count, new_id = dao.execute_sql(sql, needret=False)

    page_count = int(operator.truediv(count - 1, size)) + 1
    page = min(page, page_count)

    sql += ' limit %d offset %d' % (size, (page - 1) * size)
    print (sql)

    result, this_page_count, new_id = dao.execute_sql(sql, needdic=True)

    page = page if this_page_count > 0 else page_count

    for row in result:
        row['url'] = url_with_name(row['file_name'], thumb=True)
        row['o_url'] = url_with_name(row['file_name'])

    return result, page_count, page, size, count


def id_list(user_id, album_id, current_id=1, size=1, relation=0):
    # type: (long, long, long, int, int) -> (list, int, int, int, int)

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
        '(' + 'SELECT pic.id, pic.title, pic.description, pic.level, file.id as "fileId", file.file_name as "url" \
        FROM pic left join file on pic.file_id = file.id \
        where pic.user_id=%ld and pic.album_id=%ld %s and %s  \
        %s limit %d' + ')'

    sql = sql_format % (user_id, album_id, level_sql, 'pic.id < %ld' % current_id, 'order by pic.id desc', size)
    sql += 'UNION'
    sql += (sql_format % (user_id, album_id, level_sql, 'pic.id >= %ld' % current_id, 'order by pic.id', size + 1))

    print (sql)

    result, count, new_id = dao.execute_sql(sql, needdic=True)

    pre_id = []
    next_id = []
    for row in result:
        if row['id'] < current_id:
            next_id.append(row)
        elif row['id'] > current_id:
            pre_id.append(row)
        else:
            current = row
        row['oUrl'] = url_with_name(row['url'])
        row['url'] = url_with_name(row['url'], thumb=True)

    # pre_id.reverse()
    return True, pre_id, next_id, current


def update_info(p_id=None, user_id=None, title=None, desc=None, level=None):
    if p_id is None or user_id is None:
        return False

    p_id = int(p_id)

    sql = "UPDATE pic SET %s where id=%ld and user_id=%ld" % ('%s', p_id, user_id)

    data = []
    if title is not None:
        data.append("title='%s'" % title)
    if desc is not None:
        data.append("description='%s'" % desc)
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


def info(p_id=None, user_id=None):
    if p_id is None or user_id is None:
        return False, None

    p_id = int(p_id)
    user_id = int(user_id)

    sql = "select * from pic where id=%ld and user_id=%ld" % (p_id, user_id)
    result, count, new_id = dao.execute_sql(sql, needdic=True)
    if count > 0:
        return True, result[0]
    else:
        return False, None
