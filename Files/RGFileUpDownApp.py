# encoding: utf-8
import os

import requests
from flask import Blueprint, request, jsonify, stream_with_context, Response, json, abort, render_template
from concurrent.futures import ThreadPoolExecutor

import RGUIController
from Model import files, pic
from RGIgnoreConfig.RGFileGlobalConfigContext import FilePreFix, RemoteFileHost, name_fix, support_image
from DAO import rg_dao as dao
from RGUtil.RGCodeUtil import RGResCode
from RGUtil.RGRequestHelp import form_res, request_value, is_int_number, request_file_size

RestRouter = Blueprint('RGFileUpDown', __name__, url_prefix='/' + FilePreFix)
executor = ThreadPoolExecutor()

"""
page
"""


@RestRouter.route('/user/Desktop', methods=['GET'])
@RGUIController.auth_handler()
def desktop_page(user_id):
    return RGUIController.ui_render_template('FileSite.html')


"""
file
"""


@RestRouter.route('/upload', methods=['POST'])
@RGUIController.auth_handler()
def new_file(user_id):
    """
    上传文件
    body 参数:
        name            文件名
        type            1 文件夹 0 文件
        {file}          文件流
        {file}_md5      文件md5
        directory_id    文件位置文件夹Id
    """

    in_album = request_value(request, 'in_album', 0)
    in_file = request_value(request, 'in_file', 0)

    album_id = request_value(request, 'album_id', None)
    file_type = request_value(request, 'type')

    directory_id = request_value(request, 'directory_id', '-1')
    filename = request_value(request, 'name', '')

    # directory
    if in_file and file_type is not None and int(file_type) == 1:
        directory = files.new_directory(user_id=user_id, name=filename, directory_id=directory_id)
        if directory is None:
            return jsonify(form_res(RGResCode.insert_fail))
        else:
            return jsonify(form_res(RGResCode.ok, directory))
    # file
    if in_album:
        if album_id is None:
            return jsonify(form_res(RGResCode.lack_param))
    elif in_file:
        if not files.capacity_enough(user_id=user_id, new_file_size=request_file_size(request)):
            return jsonify(form_res(RGResCode.full_size))

    code, result = do_new_file()
    if code != RGResCode.ok:
        return jsonify(form_res(code))

    data = {}
    for res in result:
        handle = handler_upload_res(user_id, res, set_name=filename,
                                    in_album=in_album, album_id=album_id,
                                    in_file=in_file, directory_id=directory_id)

        code = handle['code']
        file_key = res['key']
        data[file_key] = {
            'code': code,
            'file': handle['data'],
        }

        if code != RGResCode.ok and 'path' in res:
            del_filename = res['path']
            executor.submit(do_del_file, [del_filename])

    return jsonify(form_res(RGResCode.ok, data))


@RestRouter.route('/fastUpload', methods=['POST'])
@RGUIController.auth_handler()
def new_user_file_with_hash(user_id):
    up_files = request_value(request, 'files')
    if up_files is None:
        return jsonify(form_res(RGResCode.lack_param))
    for file_key in up_files:
        file = up_files[file_key]
        if 'md5' not in file:
            return jsonify(form_res(RGResCode.lack_param))

        in_album = file.get('in_album', False)
        album_id = file.get('album_id', None)
        if in_album and album_id is None:
            return jsonify(form_res(RGResCode.lack_param))

    data = {}
    for file_key in up_files:
        file = up_files[file_key]
        result = __fast_up(user_id=user_id, file=file)
        data[file_key] = result
    return jsonify(form_res(RGResCode.ok, data))


def __fast_up(user_id, file):
    md5 = file['md5']
    in_album = file.get('in_album', False)
    album_id = file.get('album_id', None)
    in_file = file.get('in_file', 0)
    directory_id = file.get('directory_id', -1)
    filename = file.get('name', '')

    if in_album:
        photo, code = pic.check_and_new_pic_with_hash(user_id=user_id, file_hash=md5, filename=filename, album_id=album_id, needFullUrl=False)
        file = {"file": photo, "code": code}
    elif in_file:
        file, code = files.check_and_new_user_file_with_hash(
            user_id=user_id, directory_id=directory_id, file_hash=md5, name=filename)
        file = {"file": file, "code": code}
    else:
        conn = None
        code = RGResCode.server_error
        file_info = None
        try:
            conn = dao.get()
            file_info = files.check_file(file_hash=md5, conn=conn)
            if file_info is None:
                code = RGResCode.not_existed
                raise Exception('not existed')
            else:
                if file_info['forever'] == 0 and not files.file_set(id=file_info['id'], conn=conn, args={'forever': 1}):
                    code = RGResCode.update_fail
                    raise Exception('update fail')
            code = RGResCode.ok
            conn.commit()
        except Exception as e:
            file_info = None
            conn.rollback()
            conn.commit()
        finally:
            if conn:
                conn.close()
            if file_info is None:
                file = {"file": None, "code": code}
            else:
                file = {"file": files.filter_return_file_info(file_info=file_info, need_id=True), "code": RGResCode.ok}
    return file


@RestRouter.route('/user/list', methods=['GET'])
@RGUIController.auth_handler()
def user_file_list(user_id):
    directory_id = request_value(request, 'directory_id', -1)
    try:
        result = files.user_file_list(user_id=user_id, directory_id=directory_id)
        return jsonify(form_res(RGResCode.ok, result))
    except:
        return jsonify(form_res(RGResCode.database_error))


@RestRouter.route('/user/directory_list', methods=['GET'])
@RGUIController.auth_handler()
def user_file_directory_list(user_id):
    directory_id = request_value(request, 'directory_id', -1)
    try:
        result = files.user_file_directory_list(user_id=user_id, directory_id=directory_id)
        return jsonify(form_res(RGResCode.ok, result))
    except:
        return jsonify(form_res(RGResCode.database_error))


@RestRouter.route('/user/search', methods=['GET'])
@RGUIController.auth_handler()
def user_file_search(user_id):
    name = request_value(request, 'name')
    if name is None or len(name) <= 0:
        return jsonify(form_res(RGResCode.lack_param))
    try:
        result = files.user_file_list_with_name(user_id=user_id, name=name)
        return jsonify(form_res(RGResCode.ok, result))
    except:
        return jsonify(form_res(RGResCode.database_error))


@RestRouter.route('/user/set', methods=['POST'])
@RGUIController.auth_handler()
def user_file_set(user_id):
    id = request_value(request, 'id')
    if id is None:
        return jsonify(form_res(RGResCode.lack_param))

    args = {}
    personal_name = request_value(request, 'name')

    if personal_name is not None:
        args['personal_name'] = personal_name

    flag = files.user_file_set(user_id=user_id, id=id, args=args)
    if flag is True:
        code = RGResCode.ok
    else:
        code = RGResCode.update_fail
    return jsonify(form_res(code, None))


@RestRouter.route('/user/del', methods=['POST'])
@RGUIController.auth_handler()
def user_file_del(user_id):
    id = request_value(request, 'id')

    if id is None:
        return jsonify(form_res(RGResCode.lack_param))

    conn = None
    try:
        conn = dao.get()

        delete_files = files.user_file_del_and_return_files(user_id=user_id, id=id, conn=conn)

        if len(delete_files) > 0:
            executor.submit(do_del_file, delete_files)

        conn.commit()
        return jsonify(form_res(RGResCode.ok, None))
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()
        return jsonify(form_res(RGResCode.del_fail, None))
    finally:
        if conn:
            conn.close()


@RestRouter.route('/user/move', methods=['POST'])
@RGUIController.auth_handler()
def user_file_move(user_id):
    id = request_value(request, 'id')
    if id is None:
        return jsonify(form_res(RGResCode.lack_param))

    to_id = request_value(request, 'to_id')
    if to_id is None:
        return jsonify(form_res(RGResCode.lack_param))
    flag = files.user_file_move(user_id=user_id, move_id=id, to_id=to_id)
    if flag is True:
        code = RGResCode.ok
    else:
        code = RGResCode.del_fail
    return jsonify(form_res(code, None))


@RestRouter.route('/user/fileSize', methods=['GET'])
@RGUIController.auth_handler()
def user_file_size(user_id):
    id = request_value(request, 'id', '')
    if id is None:
        return jsonify(form_res(RGResCode.lack_param))

    error, file_size = files.user_file_size(user_id=user_id, id=id)
    if error is None:
        code = RGResCode.ok
    else:
        code = RGResCode.database_error
    return jsonify(form_res(code, {"size": file_size}))


def handler_upload_res(user_id, t, set_name=None,
                       in_album=False, album_id=-1, needFullUrl=False,
                       in_file=False, directory_id=-1):
    """

    :param user_id: userId
    :param t: 上传结果
    :param in_album: -1代表默认相册, None 代表不存入相册
    :param directory_id 文件夹id
    :return: {
            'code': code,
            'msg': err_msg,
            'file_info': file_info,
            'data': photo if in_album else user_file,
        }
    """
    file_info, user_file, photo = None, None, None
    original_name, err_msg = '', ''
    code = RGResCode.ok
    conn = None
    try:
        conn = dao.get()
        if in_file and not files.capacity_enough(user_id=user_id, new_file_size=request_file_size(request), conn=conn):
            code = RGResCode.full_size
            raise Exception('capacity not enough')
        if 'flag' in t:
            if not t['flag']:
                code = RGResCode.server_error
                raise Exception(t['err_msg'])

            exif_info = None
            exif_time, size = 0, 0
            exif_gps_lalo, mime, filename = '', '', ''

            if 'mime' in t:
                mime = t['mime']
            if 'name' in t:
                original_name = t['name']
            if 'size' in t:
                size = t['size']
            if 'path' in t:
                filename = t['path']
            if 'exif' in t:
                exif = t.get('exif', None)
                exif_time = exif.get('timestamp', None)
                exif_gps_lalo = exif.get('gps_lalo', None)
                exif_info = exif.get('original', None)
                if exif_info:
                    exif_info = json.dumps(exif_info)

            file_info = files.new_file(
                conn=conn,
                mime=mime,
                size=size,
                filename=filename,
                file_hash=t['hash'],
                exif_time=exif_time,
                exif_info=exif_info,
                exif_lalo=exif_gps_lalo,
                forever=0 if in_file else 1
            )
        if file_info is None:
            code = RGResCode.insert_fail
            raise Exception('new_file failed')

        if in_album and support_image(filename=filename):
            photo = pic.new_pic(user_id, file_info, album_id=album_id, conn=conn, title=original_name, needFullUrl=needFullUrl)
            if photo is None:
                raise Exception('new photo failed')
        elif in_file:
            user_file = files.new_user_file(
                conn=conn,
                user_id=user_id,
                file_id=file_info['id'],
                type=0,
                directory_id=directory_id,
                personal_name=set_name,
                add_timestamp=file_info['timestamp'],
                update_timestamp=file_info['timestamp'],
                combined_file_info=file_info
            )
            if user_file is None:
                code = RGResCode.insert_fail
                raise Exception('new_user_file failed')
        conn.commit()
    except Exception as e:
        print(e)
        err_msg = str(e)
        if code == RGResCode.ok:
            code = RGResCode.server_error
        conn.rollback()
        conn.commit()
    finally:
        if conn:
            conn.close()
        return {
            'code': code,
            'msg': err_msg,
            'file_info': file_info,
            'data': photo if in_album else user_file if in_file else file_info,
        }


@RestRouter.route('/user/get/<id>', methods=['GET'])
def user_file_get(id):
    if is_int_number(id):
        auth, user_id = RGUIController.do_auth()
        filename = files.user_filename(user_id=user_id, id=id)
        img_quality = request_value(request, 'img_quality', 'original')
        if img_quality == 'low':
            filename = name_fix(filename=filename, thumb=True, gif_activity=False)
        if filename is None:
            return jsonify(form_res(RGResCode.not_existed))
        return handle_download_file(filename)
    else:
        return jsonify(form_res(RGResCode.lack_param))


@RestRouter.route('/<filename>', methods=['GET'])
def handle_download_file(filename):
    remote_url = RemoteFileHost + '/' + FilePreFix + "download/" + filename
    req = requests.get(remote_url, stream=True)
    content_type = req.headers['content-type']
    print(remote_url)
    return Response(stream_with_context(req.iter_content(chunk_size=1024)), content_type=content_type)


# 博客日志导入产生的图片存放的文件
@RestRouter.route('/import/<filename>', methods=['GET'])
def handle_download_import_file(filename):
    remote_url = RemoteFileHost + '/' + FilePreFix + "download/import/" + filename
    req = requests.get(remote_url, stream=True)
    content_type = req.headers['content-type']
    print(remote_url)
    return Response(stream_with_context(req.iter_content(chunk_size=1024)), content_type=content_type)


"""
文件上传接口

接收 key 为 file, icon, background 的文件流
需要在对应的字段 file_md5, icon_md5, background_md5 提供对应的文件32位小写md5值
"""


def do_new_file():
    """
    :return: response, [{name:'', success: True}, ……, ]
    """

    url = RemoteFileHost + '/' + FilePreFix + 'upload/'
    file_stream = {}

    re_files = request.files
    for file_key in re_files:
        file_hash = request_value(request, file_key + '_md5')
        if file_hash is None:
            return RGResCode.lack_param, None
        stream = re_files[file_key]
        value = (stream.filename, stream.stream, stream.content_type)
        file_stream[file_key] = value

    print('will upload')
    req = requests.post(url=url, files=file_stream, data=request.form, params=None,
                        auth=request.authorization, cookies=request.cookies, hooks=None, json=request.json, stream=True)
    print('end upload status_code:%d' % req.status_code)

    if req.status_code == 200:
        t = req.json()
        return RGResCode.ok, t
    else:
        return RGResCode.server_error, None


def do_del_file(filenames):
    print('will delete', filenames)
    url = RemoteFileHost + '/' + FilePreFix + 'del'
    req = requests.post(url=url, json={"names": filenames})
    print('end delete status_code:%d' % req.status_code)

