from flask import Blueprint, request, jsonify, render_template, url_for, redirect

import RGUIController
from Model import user, album, pic
from RGUtil.RGCodeUtil import http_code
from RGUtil.RGRequestHelp import get_data_with_request, form_res, is_int_number

RestRouter = Blueprint('RGPhoto', __name__, url_prefix='/photo', static_folder='../static')

"""
page
"""


@RestRouter.route('/', methods=["GET"])
@RGUIController.auth_handler(page=True)
def auto_photo_page(user_id):
    url = '/photo/%ld' % user_id + '/'
    return redirect(url)


@RestRouter.route('/<other_id>/', methods=["GET"])
def photo_page(other_id):
    if is_int_number(other_id):
        auth, user_id = RGUIController.do_auth()
        if auth is True:
            return photo_page_render(user_id, other_id)
        else:
            return redirect(url_for('login_page'))
    else:
        return redirect(url_for('RGPhoto.auto_photo_page'))


def photo_page_render(user_id, other_id):
    albums, re_relation = album.album_list(user_id, other_id)
    relation = user.get_relation(user_id, other_id)
    t = {
        "list": albums,
        "user": user.get_user(other_id),
        "home": int(other_id) == int(user_id),
        "relation": relation,
        "re_relation": re_relation,
    }
    return render_template("albums.html", **t)


@RestRouter.route('/<other_id>/<album_id>', methods=["GET"])
def photos_page(other_id, album_id):
    if is_int_number(other_id) and is_int_number(album_id):
        auth, user_id = RGUIController.do_auth()
        if auth is True:
            return photos_page_render(user_id, other_id, album_id)
    return redirect(url_for('login_page'))


@RestRouter.route('/original', methods=["GET"])
def photos_original_page():
    t = get_data_with_request(request)
    return render_template("picOriginalView.html", **t)


def photos_page_render(user_id, other_id, album_id):
    t = get_data_with_request(request)
    page = t['page'] if 'page' in t else 0
    size = t['size'] if 'size' in t else 10

    relation = user.get_relation(user_id, other_id)
    re_relation = user.get_relation(other_id, user_id)

    flag, album_detail = album.album_detail(album_id=album_id, relation=relation)

    if flag is False:
        photos, page_count, now_page, page_size, count = \
            ([], 1, 1, 10, 0)
    else:
        photos, page_count, now_page, page_size, count = \
            pic.page_list(other_id, album_id, page, size, relation)

    t = {
        "list": photos,
        "pageCount": page_count,
        "pageSize": page_size,
        "nowPage": now_page,
        "count": count,
        "user": user.get_user(other_id, needIcon=True),
        "home": int(other_id) == int(user_id),
        "relation": relation,
        "re_relation": re_relation,
        'album': album_detail
    }
    return render_template("photos.html", **t)


"""
restful
"""


@RestRouter.route('edit', methods=['POST'])
@RGUIController.auth_handler(page=False)
def pic_edit(user_id):
    t = get_data_with_request(request)

    title = None
    desc = None
    level = None
    p_id = None

    if 'title' in t:
        title = t['title']

    if 'desc' in t:
        desc = t['desc']

    if 'level' in t:
        level = t['level']

    if 'id' in t:
        p_id = t['id']

    flag = pic.update_info(p_id=p_id, user_id=user_id, title=title, desc=desc, level=level)
    if flag is True:
        code = http_code.ok
    else:
        code = http_code.update_fail
    return jsonify(form_res(code, None))


@RestRouter.route('delete', methods=['POST'])
@RGUIController.auth_handler(page=False)
def pic_delete(user_id):
    t = get_data_with_request(request)
    if 'id' in t:
        p_id = t['id']
        pic.delete(user_id=user_id, p_id=p_id)
        code = http_code.ok
    else:
        code = http_code.lack_param
    return jsonify(form_res(code, None))


@RestRouter.route('album/edit', methods=['POST'])
@RGUIController.auth_handler(page=False)
def album_edit(user_id):
    t = get_data_with_request(request)

    title = None
    desc = None
    level = None
    cover = None
    album_id = None

    if 'title' in t:
        title = t['title']

    if 'desc' in t:
        desc = t['desc']

    if 'level' in t:
        level = t['level']

    if 'cover' in t:
        cover = t['cover']
        # flag, result = pic.info(p_id=pid, user_id=user_id)
        # if flag is True:
        #     cover = result['file_id']

    if 'id' in t:
        album_id = t['id']

    flag = album.update_info(album_id=album_id, user_id=user_id, title=title, desc=desc, level=level, cover=cover)
    if flag is True:
        code = http_code.ok
    else:
        code = http_code.update_fail
    return jsonify(form_res(code, None))


@RestRouter.route('album/new', methods=['POST'])
@RGUIController.auth_handler(page=False)
def album_new(user_id):
    t = get_data_with_request(request)

    title = None
    desc = None
    level = None
    cover = None

    if 'title' in t:
        title = t['title']

    if 'desc' in t:
        desc = t['desc']

    if 'level' in t:
        level = t['level']

    if 'cover' in t:
        cover = t['cover']

    flag = album.new_album(user_id=user_id, title=title, desc=desc, cover=cover, level=level)

    if flag is not None:
        code = http_code.ok
    else:
        code = http_code.update_fail
    return jsonify(form_res(code, flag))


@RestRouter.route('album/del', methods=['POST'])
@RGUIController.auth_handler(page=False)
def album_del(user_id):
    t = get_data_with_request(request)

    ids = None

    if 'ids[]' in t:
        ids = t.getlist("ids[]")

    flag = album.del_albums(user_id, ids)

    if flag is True:
        code = http_code.ok
    else:
        code = http_code.update_fail
    return jsonify(form_res(code, None))


@RestRouter.route('preList', methods=['POST'])
@RGUIController.auth_handler(page=False)
def photo_pre_list(user_id):
    t = get_data_with_request(request)

    c_id = None
    album_id = None
    size = 1

    if 'id' in t:
        c_id = t['id']

    if 'albumId' in t:
        album_id = t['albumId']

    if 'size' in t:
        size = t['size']

    flag, _album = album.album_detail(album_id, -1)

    other_id = _album['user_id']

    relation = user.get_relation(other_id, user_id)

    flag, pre_ids, next_ids, current = \
        pic.id_list(user_id=other_id, album_id=album_id, current_id=c_id, size=size, relation=relation)

    if flag is True:
        return jsonify(form_res(http_code.ok, {
            'pre': pre_ids,
            'next': next_ids,
            'current': current
        }))
    else:
        return jsonify(form_res(http_code.update_fail, None))
