from flask import Blueprint, request, jsonify, url_for, redirect

import RGUIController
from Model import article, user
from RGUtil import RGTimeUtil
from RGUtil.RGCodeUtil import RGResCode
from RGUtil.RGRequestHelp import get_data_with_request, form_res, is_int_number, request_ip

RestRouter = Blueprint('RGBlog', __name__, url_prefix='/blog', static_folder='../static')
ReadCountMap = {}

"""
page
"""


@RestRouter.route('/', methods=["GET"])
@RGUIController.auth_handler(page=True)
def auto_blog_page(user_id):
    if user_id is None:
        return redirect(url_for('login_page'))
    else:
        return  redirect(url_for('RGBlog.blog_page', other_id=user_id))


@RestRouter.route('/<other_id>/', methods=["GET"])
@RGUIController.check_bind()
def blog_page(other_id):
    if is_int_number(other_id):
        auth, view_user = RGUIController.do_auth()
        return blog_page_render(other_id, view_user)
    return redirect(url_for('login_page'))


def blog_page_render(art_user_id, view_user_id):
    relation = user.get_relation(view_user_id, art_user_id)
    re_relation = user.get_relation(art_user_id, view_user_id)
    t = {
        "user": user.get_user(art_user_id),
        "home": user.isHome(view_user_id, art_user_id),
        "authed": view_user_id is not None,
        "relation": relation,
        "re_relation": re_relation,
    }
    return RGUIController.ui_render_template("index.html", **t)


@RestRouter.route('/home/<art_user_id>', methods=["GET"])
def home_page(art_user_id):
    t = get_data_with_request(request)
    page = t['page'] if 'page' in t else 0
    size = t['size'] if 'size' in t else 10

    auth, view_user_id = RGUIController.do_auth()
    arts, page_count, now_page, page_size, count, re_relation = article.page_list(other_id=view_user_id,
                                                                                  art_user_id=art_user_id, page=page,
                                                                                  size=size)
    t = {
        "list": arts,
        "pageCount": page_count,
        "pageSize": page_size,
        "nowPage": now_page,
        "count": count,
        "home": user.isHome(view_user_id, art_user_id),
    }
    return RGUIController.ui_render_template("home.html", **t)


@RestRouter.route('/view/', methods=["GET"])
@RGUIController.auth_handler(page=True, forceLogin=False)
def auto_blog_view_page(other_id):
    return redirect(url_for('RGBlog.blog_view_page', other_id=other_id))


@RestRouter.route('/view/<other_id>/', methods=["GET"])
def blog_view_page(other_id):
    if is_int_number(other_id):
        auth, view_user_id = RGUIController.do_auth()
        return blog_view_page_render(view_user_id, other_id)
    else:
        return redirect(url_for('RGBlog.auto_blog_view_page'))


def blog_view_page_render(view_user_id, art_user_id):
    relation = user.get_relation(view_user_id, art_user_id)
    t = {
        "user": user.get_user(art_user_id),
        "relation": relation,
    }
    return RGUIController.ui_render_template("blogView.html", **t)


@RestRouter.route('/art/<art_id>', methods=['GET'])
def art_detail(art_id):
    auth, user_id = RGUIController.do_auth()

    art = article.art_detail(user_id, art_id)
    if art is not None:
        a_user_id = art['user_id']
        _user = user.get_user(a_user_id)
        home = a_user_id == user_id

        if home is False:
            collect_read_count(art_id=art_id, user_id=user_id)
    else:
        _user = None
        home = False

    return RGUIController.ui_render_template("blog_page.html", **{
        'art': art,
        'flag': art is not None,
        'home': home,
        "user": _user,
        "authed": auth,
    })


@RestRouter.route('/edit', methods=["GET"])
@RGUIController.auth_handler(page=True)
def new_blog_page(user_id):
    if user_id is not None:
        return RGUIController.ui_render_template("edit_blog.html", **{
            "user": user.get_user(user_id),
        })
    else:
        return RGUIController.ui_render_template("login.html")


@RestRouter.route('/edit/<art_id>', methods=["GET"])
def edit_blog_page_render(art_id):
    auth, user_id = RGUIController.do_auth()

    if auth is True:
        if art_id is not None:

            art = article.art_detail(user_id, art_id)
            if art is None:
                return redirect(url_for('RGBlog.new_blog_page'))

            a_user_id = art['user_id']

            if a_user_id == user_id:
                return RGUIController.ui_render_template("edit_blog.html", **{
                    'art': art,
                    "user": user.get_user(user_id),
                })
        return redirect(url_for('RGBlog.new_blog_page'))
    else:
        return RGUIController.ui_render_template("login.html")


"""
restful
"""


@RestRouter.route('/list', methods=['GET'])
@RGUIController.auth_handler()
def art_list(user_id):
    t = get_data_with_request(request)

    if 'lastId' in t:
        last_id = int(t['lastId'])
        if last_id < 0:
            last_id = None
    else:
        last_id = None

    size = t['size']

    arts, art_count, last_id = article.id_list(user_id, last_id, size)
    res = form_res(1000, {
        'art': arts,
        'count': art_count,
        'lastId': last_id,
    })
    return jsonify(res)


@RestRouter.route('/del', methods=['POST'])
@RGUIController.auth_handler()
def art_del(user_id):
    t = get_data_with_request(request)

    if 'id' in t:
        art_id = t['id']
    else:
        art_id = None

    flag, art = article.del_art(user_id, art_id)
    code = RGResCode.ok if flag is True else RGResCode.insert_fail
    res = form_res(code, None)
    return jsonify(res)


@RestRouter.route('/new', methods=['POST'])
@RGUIController.auth_handler()
def art_new(user_id):
    t = get_data_with_request(request)

    if 'id' in t:
        art_id = t['id']
    else:
        art_id = None

    if 'content' in t:
        content = t['content']
    else:
        content = ''

    if 'title' in t:
        title = t['title']
    else:
        title = None

    if 'group_id' in t:
        group_id = t['group_id']
        if len(group_id) <= 0:
            group_id = None
    else:
        group_id = None
    if 'cate' in t:
        cate = int(t['cate'])
    else:
        cate = 0

    if 'summary' in t:
        summary = t['summary']
    else:
        summary = ''

    if 'cover' in t:
        cover = t['cover']
    else:
        cover = ''

    flag, art_id = article.add_or_update_art(
        user_id=user_id,
        title=title,
        content=content,
        cate=cate,
        art_id=art_id,
        group_id=group_id,
        summary=summary,
        cover=cover
    )
    code = RGResCode.ok if flag is True else RGResCode.insert_fail
    res = form_res(code, {"id": art_id})
    return jsonify(res)


@RestRouter.route('/group/list', methods=['GET'])
@RGUIController.auth_handler(forceLogin=False)
def art_group_list(user_id):
    t = get_data_with_request(request)

    if 'userId' in t:
        other_id = t['userId']
    else:
        other_id = user_id

    relation = user.get_relation(other_id, user_id)
    flag, result = article.group_list(other_id=other_id, relation=relation)

    code = RGResCode.ok if flag is True else RGResCode.not_existed
    res = form_res(code, result)
    return jsonify(res)


@RestRouter.route('/group/rename', methods=['POST'])
@RGUIController.auth_handler()
def art_group_rename(user_id):
    t = get_data_with_request(request)

    if 'id' in t:
        group_id = t['id']
    else:
        group_id = None

    if 'name' in t:
        name = t['name']
    else:
        name = None

    flag = article.update_group_info(user_id=user_id, g_id=group_id, name=name, level=None)

    code = RGResCode.ok if flag is True else RGResCode.update_fail
    res = form_res(code, None)
    return jsonify(res)


@RestRouter.route('/group/edit', methods=['POST'])
@RGUIController.auth_handler()
def art_group_edit(user_id):
    t = get_data_with_request(request)

    if 'id' in t:
        group_id = t['id']
    else:
        group_id = None

    if 'name' in t:
        name = t['name']
    else:
        name = None

    if 'level' in t:
        level = t['level']
    else:
        level = None

    flag = article.update_group_info(user_id=user_id, g_id=group_id, name=name, level=level)

    code = RGResCode.ok if flag is True else RGResCode.update_fail
    res = form_res(code, None)
    return jsonify(res)


@RestRouter.route('/group/editOrder', methods=['POST'])
@RGUIController.auth_handler()
def art_group_edit_order(user_id):
    t = get_data_with_request(request)

    if 'ids[]' in t:
        group_ids = t.getlist('ids[]')
    else:
        group_ids = None

    if 'orders[]' in t:
        orders = t.getlist('orders[]')
    else:
        orders = None

    flag = article.update_group_order(user_id=user_id, ids=group_ids, orders=orders)

    code = RGResCode.ok if flag is True else RGResCode.update_fail
    res = form_res(code, None)
    return jsonify(res)


@RestRouter.route('/group/new', methods=['POST'])
@RGUIController.auth_handler()
def art_group_new(user_id):
    t = get_data_with_request(request)

    flag = True
    name = None

    if 'name' in t:
        name = t['name']
    else:
        flag = False

    if 'order' in t:
        order = t['order']
    else:
        order = 0

    if 'level' in t:
        level = t['level']
    else:
        level = 0

    if flag is not True:
        res = form_res(RGResCode.lack_param, None)
        return jsonify(res)

    flag, new_id = article.new_group(user_id=user_id, name=name, order=order, level=level)

    code = RGResCode.ok if flag is True else RGResCode.insert_fail
    res = form_res(code, {'id': new_id, 'user_id': user_id})
    return jsonify(res)


@RestRouter.route('/group/delete', methods=['POST'])
@RGUIController.auth_handler()
def art_group_delete(user_id):
    t = get_data_with_request(request)

    if 'id' in t:
        group_id = t['id']
    else:
        group_id = None

    flag = article.delete_group(user_id=user_id, g_id=group_id)

    code = RGResCode.ok if flag is True else RGResCode.del_fail
    res = form_res(code, None)
    return jsonify(res)


@RestRouter.route('/month/view', methods=['GET'])
@RGUIController.auth_handler(forceLogin=False)
def art_month_view(user_id):
    t = get_data_with_request(request)

    if 'user_id' in t:
        art_user = int(t['user_id'])
    else:
        art_user = None

    if 'timezone' in t:
        timezone = int(t['timezone'])
    else:
        timezone = 8

    if 'group_id' in t:
        group_id = t['group_id']
        if len(group_id) > 0:
            group_id = int(group_id)
        else:
            group_id = None
    else:
        group_id = None

    result = article.months_list_view(art_user=art_user, other_id=user_id, group_id=group_id, timezone=timezone)

    res = form_res(1000, result)
    return jsonify(res)


@RestRouter.route('/month/list', methods=['GET'])
@RGUIController.auth_handler(forceLogin=False)
def art_month_list(user_id):
    t = get_data_with_request(request)

    if 'user_id' in t:
        art_user = int(t['user_id'])
    else:
        art_user = None

    if 'timezone' in t:
        timezone = int(t['timezone'])
    else:
        timezone = 8

    if 'year' in t:
        year = int(t['year'])
    else:
        year = 1995

    if 'month' in t:
        month = int(t['month'])
    else:
        month = 1995

    if 'group_id' in t:
        group_id = t['group_id']
        if len(group_id) > 0:
            group_id = int(group_id)
        else:
            group_id = None
    else:
        group_id = None

    result = article.month_list(art_user=art_user, other_id=user_id, group_id=group_id, year=year, month=month,
                                timezone=timezone)

    res = form_res(1000, result)
    return jsonify(res)


def collect_read_count(art_id, user_id):
    timestamp = RGTimeUtil.timestamp()
    remote_addr = request_ip(request, default='')

    if art_id not in ReadCountMap:
        read_item = {
            'count': 1,
            'readers': {
                remote_addr: {
                    'time': timestamp,
                }
            }
        }
        if user_id is not None:
            read_item['readers'][user_id] = {'time': timestamp}
        ReadCountMap[art_id] = read_item
    else:

        read_item = ReadCountMap[art_id]
        readers = read_item['readers']
        reader = None

        if user_id is not None:
            if user_id in readers:
                reader = readers[user_id]
            else:
                reader = {'time': 0}
                readers[user_id] = reader

        if remote_addr in readers:
            reader_ip = readers[remote_addr]
        else:
            reader_ip = {'time': 0}
            readers[remote_addr] = reader_ip

        read_time = timestamp
        if reader is not None:
            read_time = reader['time']
        elif reader_ip is not None:
            read_time = reader_ip['time']

        if timestamp - read_time > 60 * 60 * 1000:
            read_item['count'] = read_item['count'] + 1
            reader_ip['time'] = timestamp
            if reader is not None:
                reader['time'] = timestamp

    # print(ReadCountMap)


@RestRouter.route('/applyReadCount', methods=['POST'])
def apply_read_count():
    if request_ip(request, default=request.remote_addr) != '127.0.0.1':
        return jsonify(form_res(-1))

    ids = []
    counts = []

    for art_id, read_item in ReadCountMap.items():
        # readers = read_item['readers']
        count = read_item['count']
        if count > 0:
            counts.append(count)
            ids.append(art_id)
            read_item['count'] = 0

    article.add_art_read_count(ids, counts)
    res = form_res(1000)
    return jsonify(res)
