# encoding: utf-8
import operator
from datetime import datetime

import pymysql
from goose import Goose
from goose.text import StopWordsChinese

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
    try:
        conn = dao.get()
        cursor = conn.cursor()
        count = cursor.execute('SELECT * FROM art where user_id=%ld order by id desc ' % user_id)
        result = cursor.fetchmany(1)
        if last_id is None and count > 0:
            last_id = result[0][0] + 1
        conn.commit()
    except Exception as ex:
        return None, 0, 0
    finally:
        cursor.close()

    sql = 'SELECT * FROM art where user_id=%ld AND id < %ld order by id desc limit %d' % \
          (int(user_id), int(last_id), int(size))
    result, count, new_id = dao.execute_sql(sql)

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


def page_list(user_id, other_id=-1, page=1, size=10, dic=True):
    size = int(size)

    user_id = long(user_id)
    other_id = long(other_id)
    relation = 0

    page = int(page)
    if page < 1:
        page = 1

    if user_id != other_id:
        relation = user.get_relation(other_id, user_id)

        if relation == 0:
            sql = 'SELECT * FROM art where user_id=%ld and cate=0 order by id desc' % other_id
        elif relation == 1:
            sql = 'SELECT * FROM art where user_id=%ld and cate<=1 order by id desc' % other_id
        else:
            return None, 0, 0, 0, 0, relation
    else:
        sql = 'SELECT * FROM art where user_id=%ld order by id desc' % other_id

    result, count, new_id = dao.execute_sql(sql, needret=False)

    page_count = int(operator.truediv(count - 1, size)) + 1
    page = min(page, page_count)

    sql += ' limit %d offset %d' % (size, (page - 1) * size)
    print sql

    result, this_page_count, new_id = dao.execute_sql(sql)

    page = page if this_page_count > 0 else page_count
    objects_list = []

    for row in result:
        d = art_obj_with_sqlresult(row)
        if dic:
            objects_list.append(d.__dict__)
        else:
            objects_list.append(d)

    return objects_list, page_count, page, size, count, relation


def months_list_view(user_id=None, other_id=None, group_id=None, timezone=8):
    if user_id == other_id:
        sql = 'SELECT date_format(CONVERT_TZ(create_time, @@session.time_zone, "%+d:00"), "%s") months, count(id) as "count" \
                      FROM art where user_id=%ld %s \
                      group by months order by months desc' % (timezone, '%s', user_id, '%s')
    else:
        sql = 'SELECT date_format(CONVERT_TZ(create_time, @@session.time_zone, "%+d:00"), "%s") months, count(id) as "count" \
                    FROM art where user_id=%ld and ( \
                    cate <= (select relation from user_relation where m_user_id = %ld and o_user_id = %ld) \
                    or \
                    cate <= 0 \
                    ) \
                    %s \
                    group by months order by months desc' % (timezone, '%s', user_id, user_id, other_id, '%s')

    time_format = '%Y-%m'
    if group_id is None:
        sql = sql % (time_format, '')
    elif group_id < 0:
        sql = sql % (time_format, 'and (group_id is null or group_id not in (SELECT id from art_group))')
    else:
        sql = sql % (time_format, 'and group_id=%ld' % group_id)

    result, count, new_id = dao.execute_sql(sql, needdic=True)

    return result


def month_list(user_id, other_id, group_id, year, month, timezone=8):
    s_time = RGTimeUtil.timestamp_with_month(year=year, month=month, timezone=timezone)

    if month + 1 >= 13:
        year += 1
        month = 1
    else:
        month += 1

    e_time = RGTimeUtil.timestamp_with_month(year=year, month=month, timezone=timezone)

    if user_id == other_id:
        sql = 'select * from art \
        where user_id=%ld and \
        addtime >= %ld and addtime < %ld %s order by addtime desc' % (user_id, s_time, e_time, '%s')
    else:
        sql = 'select * from art \
                where \
                user_id=%ld and \
                addtime >= %ld and addtime < %ld and \
                ( \
                cate <= (select relation from user_relation where m_user_id = %ld and o_user_id = %ld) \
                or \
                cate <= 0 \
                ) \
                %s \
                order by addtime desc' % (user_id, s_time, e_time, user_id, other_id, '%s')

    if group_id is None:
        sql = sql % ''
    elif group_id < 0:
        sql = sql % 'and (group_id is null or group_id not in (SELECT id from art_group))'
    else:
        sql = sql % ('and group_id=%ld' % group_id)
    print sql
    result, count, new_id = dao.execute_sql(sql, needdic=True)

    return result


def add_or_update_art(user_id, title=None, content='', cate=0, group_id='', art_id=None, summary='', cover=''):
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

    if len(summary) >= 0:
        summary = pymysql.escape_string(summary)
    if content and len(content) >= 0:
        content = pymysql.escape_string(content)
    if title and len(title) >= 0:
        title = pymysql.escape_string(title)
    if cover and len(cover) >= 0:
        cover = pymysql.escape_string(cover)

    if 'image' in open_graph:
        p_cover = open_graph['image']
    if p_cover is '' and art_parse.top_image is not None:
        p_cover = art_parse.top_image.src
    if p_cover is not None and len(p_cover) is not 0:
        cover = p_cover

    if len(group_id) <= 0:
        group_id = 'null'
    else:
        group_id = str(group_id)

    if art_id is None:
        sql = "INSERT INTO art \
            (title, summary, cate, user_id, group_id, cover, content, addtime, updatetime, create_time)\
             VALUES ('%s', '%s', %d, %ld, %s, '%s', '%s', %ld, %ld, from_unixtime(%ld))" % \
              (title, summary, cate, user_id, group_id, cover, content, timestamp, timestamp, timestamp / 1000)
    else:
        art_id = long(art_id)
        sql = "UPDATE art SET \
                title = '%s', summary='%s', cate=%d, \
                user_id=%ld, group_id=%s, cover='%s', \
                content='%s', updatetime=%ld, group_id=%s \
                WHERE id=%ld and user_id =%ld" % \
              (title, summary, cate,
               user_id, group_id, cover,
               content, timestamp, group_id,
               art_id, user_id)

    result, count, new_id = dao.execute_sql(sql, needdic=True, neednewid=True)

    if count > 0:
        return True, art_id if art_id is not None else new_id
    else:
        return False, 0


def del_art(user_id, art_id=None):
    if art_id is None or art_id is '':
        return False, 0

    art_id = long(art_id)
    sql = "DELETE from art where id=%ld and user_id=%ld" \
          % (art_id, user_id)

    result, count, new_id = dao.execute_sql(sql)

    if count > 0:
        return True, art_id
    else:
        return False, 0


def art_detail(user_id, art_id):
    user_id = long(user_id)
    art_id = long(art_id)

    sql = \
        'SELECT art.id, art.title, art.summary, \
            art.cate, art.user_id, art.cover, \
            art.content, art.addtime, art.updatetime, \
            art_group.name as "group_name", art_group.id as "group_id"\
        FROM art left join art_group on art_group.id = art.group_id\
        where art.id = %ld and (\
            (art.cate = 0)\
            or\
            (art.user_id = %ld)\
            or\
            (art.user_id in (select user_relation.m_user_id\
                            from user_relation\
                            where m_user_id = art.user_id and o_user_id = %ld and relation >= art.cate))\
            )' % (art_id, user_id, user_id)

    result, count, new_id = dao.execute_sql(sql, needdic=True)
    if count:
        return result[0]
    return None


def new_group(user_id=None, name='', order=0, level=0):
    user_id = long(user_id)
    order = int(order)
    name = dao.escape_string(name)

    sql = 'insert into art_group (name, user_id, `order`, level) values ("%s", %ld, %d, %d)' % (
        name, user_id, order, level)
    result, count, new_id = dao.execute_sql(sql, neednewid=True)
    if count:
        return True, new_id
    else:
        return False, -1


def update_group_info(user_id=None, g_id=None, name=None, level=None):
    user_id = long(user_id)
    g_id = long(g_id)

    sql = "UPDATE art_group SET %s where id=%ld and user_id=%ld" % ('%s', g_id, user_id)

    data = []
    if name:
        name = dao.escape_string(name)
        data.append("name='%s'" % name)
    if level:
        level = int(level)
        data.append("level=%d" % level)

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


def update_group_order(user_id=None, ids=None, orders=None):
    try:
        user_id = long(user_id)

        sql = "UPDATE art_group SET `order` = case id \
          %s where id in (%s) and user_id=%ld" % ('%s', '%s', user_id)

        case = ''

        for index in range(len(ids)):
            gid = long(ids[index])
            order = long(orders[index])
            case += ('when %ld then %ld ' % (gid, order))
        case += 'end'

        update_ids = ",".join(str(i) for i in ids)

        sql = sql % (case, update_ids)
        dao.execute_sql(sql, needret=False)
        return True
    except:
        return False


def group_list(other_id=None, relation=0):
    if relation != -1:
        if relation == 0:
            sql = 'SELECT * FROM art_group where user_id=%ld and level=0' % other_id
        elif relation == 1:
            sql = 'SELECT * FROM art_group where user_id=%ld and level<=1' % other_id
        else:
            return True, None
    else:
        sql = 'SELECT * FROM art_group where user_id=%ld' % other_id

    sql += " order by `order` desc, id asc"
    result, count, new_id = dao.execute_sql(sql, needdic=True)
    if count:
        return True, result
    else:
        return True, []


def delete_group(user_id=None, g_id=None):
    user_id = long(user_id)
    g_id = long(g_id)

    sql = 'delete from art_group where user_id=%ld and id=%ld' % (user_id, g_id)
    result, count, new_id = dao.execute_sql(sql)
    if count:
        return True
    else:
        return False
