# encoding: utf-8
import operator
from urllib import parse

from goose3 import Goose
from goose3.text import StopWordsChinese

from DAO import rg_dao as dao
from Model import user
from RGUtil import RGTimeUtil


def id_list(user_id, last_id=None, size=10):
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
    result, count, new_id = dao.execute_sql(sql, kv=True,
                                            args={'user_id': user_id, 'last_id': last_id, 'size': size})

    last_id = 0
    for row in result:
        last_id = row['id']

    return result, count, last_id if count > 0 else 0


def page_list(other_id=None, art_user_id=-1, page=1, size=10):
    size = int(size)

    relation = -1

    page = int(page)
    if page < 1:
        page = 1

    if other_id is None:
        sql = 'select art.* from art left join art_group as g on g.id = art.group_id \
                        where \
                        art.user_id=%(art_user)s \
                        and cate <= 0 \
                        and (g.id is NULL or g.level <= 0) \
                        order by addtime desc'
        relation = 0
    elif user.isHome(art_user_id, other_id):
        relation = 2
        sql = 'select art.* from art where user_id=%(art_user)s order by addtime desc'
    else:
        sql = 'select art.*, relation from art \
                left join art_group as g on g.id = art.group_id \
                left join (select relation from user_relation \
                            where m_user_id = %(art_user)s and o_user_id = %(other_id)s) as r on 1=1 \
                where \
                art.user_id=%(art_user)s \
                and (g.id is NULL or g.level <= 0 or g.level <= r.relation) \
                and (cate <= 0 or cate <= r.relation) \
                order by addtime desc'

    args = {
        'art_user': art_user_id,
        'other_id': other_id,
    }
    result, count, new_id = dao.execute_sql(sql, ret=False, args=args)

    page_count = int(operator.truediv(count - 1, size)) + 1
    page = min(page, page_count)

    sql += ' limit %d offset %d' % (size, (page - 1) * size)

    result, this_page_count, new_id = dao.execute_sql(sql, kv=True, args=args)

    page = page if this_page_count > 0 else page_count

    if result is not None:
        for row in result:
            if relation == -1 and 'relation' in row:
                relation = row['relation']
                if relation is None:
                    relation = 0
            del row['content']

    return result, page_count, page, size, count, relation


def months_list_view(art_user=None, other_id=None, group_id=None, timezone=8):
    timezone = '%+d' % timezone
    time_format = '%%Y-%%m'

    if other_id is None:
        sql = 'SELECT date_format(CONVERT_TZ(create_time, @@session.time_zone, "{}:00"), "{}") months, count(art.id) as "count" \
                            FROM art \
                                left join art_group as g on g.id = art.group_id \
                            where \
                            art.user_id=%(art_user)s \
                            and cate <= 0 \
                            and (g.id is NULL or g.level <= 0) \
                            {} \
                            group by months order by months desc'.format(timezone, time_format, '{}')
    elif user.isHome(art_user, other_id):
        sql = 'SELECT date_format(CONVERT_TZ(create_time, @@session.time_zone, "{}:00"), "{}") months, count(art.id) as "count" \
                      FROM art where user_id=%(art_user)s {} \
                      group by months order by months desc'.format(timezone, time_format, '{}')
    else:
        sql = 'SELECT date_format(CONVERT_TZ(create_time, @@session.time_zone, "{}:00"), "{}") months, count(art.id) as "count" \
                    FROM art \
                        left join art_group as g on g.id = art.group_id \
                        left join (select relation from user_relation \
                                    where m_user_id = %(art_user)s and o_user_id = %(other_id)s) as r on 1=1 \
                    where art.user_id=%(art_user)s \
                    and (g.id is NULL or g.level <= 0 or g.level <= r.relation) \
                    and (cate <= 0 or cate <= r.relation) \
                    {} \
                    group by months order by months desc'.format(timezone, time_format, '{}')

    if group_id is None:
        sql = sql.format('')
    elif group_id < 0:
        sql = sql.format('and (group_id is null or group_id not in (SELECT id from art_group))')
    else:
        sql = sql.format('and group_id=%(group_id)s')

    result, count, new_id = dao.execute_sql(sql, kv=True, args={
        'art_user': art_user,
        'other_id': other_id,
        'group_id': group_id,
    })
    return result


def month_list(art_user, other_id, group_id, year, month, timezone=8):
    s_time = RGTimeUtil.timestamp_with_month(year=year, month=month, timezone=timezone)

    if month + 1 >= 13:
        year += 1
        month = 1
    else:
        month += 1

    e_time = RGTimeUtil.timestamp_with_month(year=year, month=month, timezone=timezone)

    item = "art.id, art.title, art.summary, art.cate, art.cover, \
        art.addtime, art.updatetime, art.create_time, art.read_count, art.group_id"

    if other_id is None:
        sql = 'select {} from art \
                            left join art_group as g on g.id = art.group_id \
                        where \
                        art.user_id=%(art_user)s \
                        and addtime >= {} \
                        and addtime < {} \
                        and cate <= 0 \
                        and (g.id is NULL or g.level <= 0) \
                        {} \
                        order by addtime desc'.format(item, s_time, e_time, '{}')
    elif user.isHome(art_user, other_id):
        sql = 'select {} from art \
                where user_id=%(art_user)s and \
                addtime >= {} and addtime < {} {} order by addtime desc'.format(item, s_time, e_time, '{}')
    else:
        sql = 'select {} from art \
                left join art_group as g on g.id = art.group_id \
                left join (select relation from user_relation \
                            where m_user_id = %(art_user)s and o_user_id = %(other_id)s) as r on 1=1 \
                where \
                art.user_id=%(art_user)s \
                and addtime >= {} \
                and addtime < {} \
                and (g.id is NULL or g.level <= 0 or g.level <= r.relation) \
                and (cate <= 0 or cate <= r.relation) \
                {} \
                order by addtime desc'.format(item, s_time, e_time, '{}')

    if group_id is None:
        sql = sql.format('')
    elif group_id < 0:
        sql = sql.format('and (group_id is null or group_id not in (SELECT id from art_group))')
    else:
        sql = sql.format('and group_id=%(group_id)s')

    result, count, new_id = dao.execute_sql(sql, kv=True, args={
        'art_user': art_user,
        'other_id': other_id,
        'group_id': group_id,
    })
    return result


def add_or_update_art(user_id, title=None, content='', cate=0, group_id=None, art_id=None, summary='', cover='',
                      conn=None, commit=True, timestamp=None):
    if timestamp is None:
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
    if p_summary is not None and len(p_summary) == 0:
        p_summary = art_parse.cleaned_text
    if p_summary is not None and len(p_summary) != 0:
        summary = p_summary

    if len(summary) >= 100:
        summary = summary[:97] + '...'

    if 'image' in open_graph:
        p_cover = open_graph['image']
    if p_cover == '' and art_parse.top_image is not None:
        p_cover = art_parse.top_image.src
    if p_cover is not None and len(p_cover) != 0:
        cover = p_cover
    # if cover is not None and len(cover) > 0:
    #     try:
    #         parsed_tuple = parse.urlparse(cover)
    #         if parsed_tuple.netloc.endswith(RGDomainName) or parsed_tuple.hostname is None:
    #             p_cover = parsed_tuple.path
    #             index = p_cover.find(FilePreFix)
    #             if index == 0 or index == 1:
    #                 cover = p_cover
    #                 index = cover.rfind(RGQualityName+'.')
    #                 if index != -1:
    #                     cover = cover[0:index] + RGThumbnailName + cover[index+len(RGQualityName):]
    #     except Exception as e:
    #         print(e)

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

    args = {
        'title': title,
        'summary': summary,
        'cate': cate,
        'user_id': user_id,
        'group_id': group_id,
        'cover': cover,
        'content': content,
        'timestamp': timestamp,
        'art_id': art_id,
    }

    result, count, new_id, err = dao.do_execute_sql(
        sql=sql,
        kv=True,
        new_id=True,
        conn=conn,
        commit=commit,
        args=args
    )

    if count > 0:
        return True, art_id if art_id is not None else new_id
    else:
        return False, 0


def del_art(user_id, art_id=None):
    if art_id is None or art_id == '':
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
            art.content, art.addtime, art.updatetime, art.read_count, \
            art_group.name as "group_name", art_group.id as "group_id", art_group.level as "group_level"\
        FROM art \
            left join art_group on art_group.id = art.group_id\
            left join user_relation as r on r.m_user_id = art.user_id  and r.o_user_id=%(other_id)s \
        where art.id = %(art_id)s and ((art.user_id = %(other_id)s) or\
            (art_group.id is NULL \
            or \
            art_group.level <= 0 \
            or \
            art_group.level <= r.relation \
            ) \
            and (\
            art.cate <= 0\
            or \
            art.cate <= r.relation \
            ))'

    result, count, new_id = dao.execute_sql(sql, kv=True, args={
        'art_id': art_id,
        'other_id': user_id
    })
    if count:
        art = result[0]
        art['logicCate'] = max(art['cate'], art['group_level'] if art['group_level'] is not None else 0)
        return result[0]
    return None


def new_group_sql():
    return 'insert into art_group (name, user_id, `order`, level) values (%(name)s, %(user_id)s, %(order)s, %(level)s)'


def new_group(user_id=None, name='', order=0, level=0):
    sql = new_group_sql()
    result, count, new_id = dao.execute_sql(sql, new_id=True, args={
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
    result, count, new_id = dao.execute_sql(sql, ret=False, args={
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
        dao.execute_sql(sql, ret=False, args={
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
    result, count, new_id = dao.execute_sql(sql, kv=True, args={
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


def add_art_read_count(ids=None, counts=None):
    try:
        sql = "UPDATE art SET `read_count` = `read_count` + case id \
        {} where id in ({})".format('{}', '{}')

        case = ''
        update_ids = ''

        for index in range(len(ids)):
            a_id = int(ids[index])
            count = int(counts[index])
            if count != 0:
                case += ('when %ld then %ld ' % (a_id, count))
                if index == 0:
                    update_ids += '{}'.format(a_id)
                else:
                    update_ids += ',{}'.format(a_id)

        if len(update_ids) <= 0:
            return True

        case += 'end'

        sql = sql.format(case, update_ids)
        dao.execute_sql(sql, ret=False)
        return True
    except:
        return False
