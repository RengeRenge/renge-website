# encoding: utf-8
import operator
from datetime import datetime

import pymysql
from goose3 import Goose
from goose3.text import StopWordsChinese

from DAO import rg_dao as dao
from Model import user
from RGUtil import RGTimeUtil


class article:
    def __init__(self, ID, title, summary, cate, userId, groupId, cover, content, addTime, updateTime, create_time):
        self.ID = ID
        self.title = title
        self.summary = summary
        self.addTime = addTime
        self.cate = int(cate)
        self.userId = userId
        self.groupId = groupId
        self.cover = cover
        self.content = content
        # self.addTime = addTime
        self.addTime = RGTimeUtil.timestamp(date=create_time)
        self.updateTime = updateTime
        self.createTime = create_time


def art_obj_with_sqlresult(result, needContent=False):
    art = article(
        result[0],
        result[1],
        result[2],
        result[3],
        result[4],
        result[5],
        result[6],
        result[7] if needContent else None,
        result[8],
        result[9],
        result[10]
    )
    return art


def id_list(user_id, last_id=None, size=10, dic=True):
    conn = None
    cursor = None
    try:
        conn = dao.get()
        cursor = conn.cursor()
        count = cursor.execute('SELECT * FROM art where user_id=%(user_id)s order by id desc', {'user_id': user_id})
        result = cursor.fetchmany(1)
        if last_id is None and count > 0:
            last_id = result[0][0] + 1
        conn.commit()
    except Exception as ex:
        conn.rollback()
        conn.commit()
        return None, 0, 0
    finally:
        dao.close(conn, cursor)

    sql = 'SELECT * FROM art where user_id=%(user_id)s AND id < %(last_id)s order by id desc limit %(size)s'
    result, count, new_id = dao.execute_sql(sql, args={'user_id': user_id, 'last_id': last_id, 'size': size})

    objects_list = []
    last_id = 0
    for row in result:
        d = art_obj_with_sqlresult(row)
        last_id = d.ID
        if dic:
            objects_list.append(d.__dict__)
        else:
            objects_list.append(d)

    return objects_list, count, last_id if count > 0 else 0


def page_list(user_id=None, art_user_id=-1, page=1, size=10, dic=True):
    size = int(size)

    relation = 0

    page = int(page)
    if page < 1:
        page = 1

    if user.isHome(user_id, art_user_id):
        sql = 'SELECT * FROM art where user_id=%(art_user_id)s order by id desc'
    else:
        if user_id is not None:
            relation = user.get_relation(art_user_id, user_id)

        if relation == 0:
            sql = 'SELECT * FROM art where user_id=%(art_user_id)s and cate=0 order by id desc'
        elif relation == 1:
            sql = 'SELECT * FROM art where user_id=%(art_user_id)s and cate<=1 order by id desc'
        else:
            return None, 0, 0, 0, 0, relation

    result, count, new_id = dao.execute_sql(sql, needret=False, args={'art_user_id': art_user_id})

    page_count = int(operator.truediv(count - 1, size)) + 1
    page = min(page, page_count)

    sql += ' limit %d offset %d' % (size, (page - 1) * size)
    print(sql)

    result, this_page_count, new_id = dao.execute_sql(sql, args={'art_user_id': art_user_id})

    page = page if this_page_count > 0 else page_count
    objects_list = []

    if result is not None:
        for row in result:
            d = art_obj_with_sqlresult(row)
            if dic:
                objects_list.append(d.__dict__)
            else:
                objects_list.append(d)

    return objects_list, page_count, page, size, count, relation


def months_list_view(art_user=None, other_id=None, group_id=None, timezone=8):
    if other_id is None:
        sql = 'SELECT date_format(CONVERT_TZ(create_time, @@session.time_zone, "%+d:00"), "%s") months, count(id) as "count" \
                            FROM art where user_id=%ld and cate <= 0 \
                            %s \
                            group by months order by months desc' % (timezone, '%s', art_user, '%s')
    elif user.isHome(art_user, other_id):
        sql = 'SELECT date_format(CONVERT_TZ(create_time, @@session.time_zone, "%+d:00"), "%s") months, count(id) as "count" \
                      FROM art where user_id=%ld %s \
                      group by months order by months desc' % (timezone, '%s', art_user, '%s')
    else:
        sql = 'SELECT date_format(CONVERT_TZ(create_time, @@session.time_zone, "%+d:00"), "%s") months, count(id) as "count" \
                    FROM art where user_id=%ld and ( \
                    cate <= (select relation from user_relation where m_user_id = %ld and o_user_id = %ld) \
                    or \
                    cate <= 0 \
                    ) \
                    %s \
                    group by months order by months desc' % (timezone, '%s', art_user, art_user, other_id, '%s')

    time_format = '%Y-%m'
    if group_id is None:
        sql = sql % (time_format, '')
    elif group_id < 0:
        sql = sql % (time_format, 'and (group_id is null or group_id not in (SELECT id from art_group))')
    else:
        sql = sql % (time_format, 'and group_id=%ld' % group_id)

    result, count, new_id = dao.execute_sql(sql, needdic=True)

    return result


def month_list(art_user, other_id, group_id, year, month, timezone=8):
    s_time = RGTimeUtil.timestamp_with_month(year=year, month=month, timezone=timezone)

    if month + 1 >= 13:
        year += 1
        month = 1
    else:
        month += 1

    e_time = RGTimeUtil.timestamp_with_month(year=year, month=month, timezone=timezone)

    if other_id is None:
        sql = 'select * from art \
                        where \
                        user_id=%(art_user)s and \
                        addtime >= {} and addtime < {} and cate <= 0 \
                        {} \
                        order by addtime desc'.format(s_time, e_time, '{}')
    elif user.isHome(art_user, other_id):
        sql = 'select * from art \
                where user_id=%(art_user)s and \
                addtime >= {} and addtime < {} {} order by addtime desc'.format(s_time, e_time, '{}')
    else:
        sql = 'select * from art \
                where \
                user_id=%(art_user)s and \
                addtime >= {} and addtime < {} and \
                ( \
                    cate <= \
                    (select relation from user_relation where m_user_id = %(art_user)s and o_user_id = %(other_id)s) \
                    or \
                    cate <= 0 \
                ) \
                {} \
                order by addtime desc'.format(s_time, e_time, '{}')

    if group_id is None:
        sql = sql.format('')
    elif group_id < 0:
        sql = sql.format('and (group_id is null or group_id not in (SELECT id from art_group))')
    else:
        sql = sql.format('and group_id=%(group_id)s')
    print(sql)
    result, count, new_id = dao.execute_sql(sql, needdic=True, args={
        'art_user': art_user,
        'other_id': other_id,
        'group_id': group_id,
    })
    return result


def add_or_update_art(user_id, title=None, content='', cate=0, group_id=None, art_id=None, summary='', cover=''):
    timestamp = RGTimeUtil.timestamp()

    g = Goose(
        {'browser_user_agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)\
         Chrome/57.0.2987.110 Safari/537.36',
         'stopwords_class': StopWordsChinese
         })

    h5_format = \
        '<!DOCTYPE html> \
        <html lang = "zh"> \
        <head> \
        <meta charset = "UTF-8"> \
        <title> blog </title > \
        </head> \
        <body> \
        <article><div> %s </div></article> \
        </body> \
        </html>'

    art_parse = g.extract(raw_html=h5_format % content)
    open_graph = art_parse.opengraph

    p_summary = ''
    p_cover = ''

    if 'description' in open_graph:
        p_summary = open_graph['description']
    if p_summary is not None and len(p_summary) is 0:
        p_summary = art_parse.cleaned_text
    if p_summary is not None and len(p_summary) is not 0:
        summary = p_summary

    if len(summary) >= 100:
        summary = summary[:97] + '...'

    if 'image' in open_graph:
        p_cover = open_graph['image']
    if p_cover is '' and art_parse.top_image is not None:
        p_cover = art_parse.top_image.src
    if p_cover is not None and len(p_cover) is not 0:
        cover = p_cover

    if group_id is not None and int(group_id) < 0:
        group_id = None

    if art_id is None:
        sql = "INSERT INTO art \
            (title, summary, cate, user_id, group_id, cover, content, addtime, updatetime, create_time) \
             VALUES (%(title)s, %(summary)s, %(cate)s, %(user_id)s, %(group_id)s, %(cover)s, %(content)s, \
             {}, {}, from_unixtime({}))".format(timestamp, timestamp, timestamp / 1000)
    else:
        art_id = int(art_id)
        sql = "UPDATE art SET \
                title = %(title)s, summary=%(summary)s, cate=%(cate)s, \
                user_id=%(user_id)s, group_id=%(group_id)s, cover=%(cover)s, \
                content=%(content)s, updatetime=%(timestamp)s, group_id=%(group_id)s \
                WHERE id=%(art_id)s and user_id =%(user_id)s"

    result, count, new_id = dao.execute_sql(sql, needdic=True, neednewid=True, args={
        'title': title,
        'summary': summary,
        'cate': cate,
        'user_id': user_id,
        'group_id': group_id,
        'cover': cover,
        'content': content,
        'timestamp': timestamp,
        'art_id': art_id,
    })

    if count > 0:
        return True, art_id if art_id is not None else new_id
    else:
        return False, 0


def del_art(user_id, art_id=None):
    if art_id is None or art_id is '':
        return False, 0

    sql = "DELETE from art where id=%(art_id)s and user_id=%(user_id)s"

    result, count, new_id = dao.execute_sql(sql, args={
        'art_id': art_id,
        'user_id': user_id
    })

    if count > 0:
        return True, art_id
    else:
        return False, 0


def art_detail(user_id, art_id):
    sql = \
        'SELECT art.id, art.title, art.summary, \
            art.cate, art.user_id, art.cover, \
            art.content, art.addtime, art.updatetime, \
            art_group.name as "group_name", art_group.id as "group_id"\
        FROM art left join art_group on art_group.id = art.group_id\
        where art.id = %(art_id)s and (\
            (art.cate = 0)\
            or\
            (art.user_id = %(user_id)s)\
            or\
            (art.user_id in (select user_relation.m_user_id\
                            from user_relation\
                            where m_user_id = art.user_id and o_user_id = %(user_id)s and relation >= art.cate))\
            )'
    result, count, new_id = dao.execute_sql(sql, needdic=True, args={
        'art_id': art_id,
        'user_id': user_id
    })
    if count:
        return result[0]
    return None


def new_group(user_id=None, name='', order=0, level=0):
    sql = 'insert into art_group (name, user_id, `order`, level) values (%(name)s, %(user_id)s, %(order)s, %(level)s)'
    result, count, new_id = dao.execute_sql(sql, neednewid=True, args={
        'name': name,
        'user_id': user_id,
        'order': order,
        'level': level
    })
    if count:
        return True, new_id
    else:
        return False, -1


def update_group_info(user_id=None, g_id=None, name=None, level=None):
    sql = 'UPDATE art_group SET {} where id=%(g_id)s and user_id=%(user_id)s'.format('{}')

    data = []
    if name:
        data.append("name=%(name)s")
    if level:
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
        'level': level,
        'name': name,
        'user_id': user_id,
        'g_id': g_id
    })
    if count > 0:
        return True
    else:
        return False


def update_group_order(user_id=None, ids=None, orders=None):
    try:
        sql = "UPDATE art_group SET `order` = case id \
          {} where id in ({}) and user_id=%(user_id)s".format('{}', '{}')

        case = ''

        for index in range(len(ids)):
            gid = int(ids[index])
            order = int(orders[index])
            case += ('when %ld then %ld ' % (gid, order))
        case += 'end'

        update_ids = ",".join(str(i) for i in ids)

        sql = sql.format(case, update_ids)
        dao.execute_sql(sql, needret=False, args={
            'user_id': user_id
        })
        return True
    except:
        return False


def group_list(other_id=None, relation=0):
    if relation != -1:
        if relation == 0:
            sql = 'SELECT * FROM art_group where user_id=%(other_id)s and `level`=0'
        elif relation == 1:
            sql = 'SELECT * FROM art_group where user_id=%(other_id)s and `level`<=1'
        else:
            return True, None
    else:
        sql = 'SELECT * FROM art_group where user_id=%(other_id)s'

    sql += " order by `order` desc, id asc"
    result, count, new_id = dao.execute_sql(sql, needdic=True, args={
        'other_id': other_id
    })
    if count:
        return True, result
    else:
        return True, []


def delete_group(user_id=None, g_id=None):
    sql1 = 'delete from art_group where user_id=%(user_id)s and id=%(g_id)s'
    args1 = {
        'user_id': user_id,
        'g_id': g_id
    }

    sql2 = 'update art set group_id = null where group_id=%(g_id)s'
    args2 = {
        'user_id': user_id,
        'g_id': g_id
    }
    result = dao.execute_sqls(
        sqls=[(sql1, args1), (sql2, args2)],
    )
    if result is not None:
        return True
    else:
        return False
