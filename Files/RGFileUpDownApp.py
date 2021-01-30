# encoding: utf-8
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

import requests
from flask import Blueprint, request, jsonify, stream_with_context, Response, json, redirect, \
    url_for

import RGUIController
from DAO import rg_dao as dao
from Files import RGFileOpen
from Model import files, pic
from RGIgnoreConfig.RGFileGlobalConfigContext import FilePreFix, RemoteFileHost, name_fix, support_image
from RGUtil import RGRequestHelp
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


@RestRouter.route('/nyapass/pv<user_file_id>', methods=['GET'])
def video_view_page(user_file_id):
    if is_int_number(user_file_id):
        user_file_id = int(user_file_id)
        auth, user_id = RGUIController.do_auth()
        if not auth:
            return redirect(url_for('login_page'))
        if user_file_id == -1 or files.user_file_info(user_id=user_id, id=user_file_id, type=1) is not None:
            code = RGRequestHelp.did_encode(user_file_id, user_id)
            return redirect(url_for('RGFileUpDown.play_list_page', user_id_directory_id=code))
    return RGUIController.ui_render_template('VideoPreview.html')


@RestRouter.route('/nyapass/playList/pv<user_id_directory_id>', methods=['GET'])
def play_list_page(user_id_directory_id):
    auth, user_id = RGUIController.do_auth()
    if not auth:
        return redirect(url_for('login_page'))
    return RGUIController.ui_render_template('VideoPreview.html')


@RestRouter.route('/nyapass/sv<open_code>', methods=['GET'])
def share_page(open_code):
    try:
        f_id, u_id = RGRequestHelp.fid_decode(open_code)
        file_info = files.user_file_info(user_id=u_id, id=f_id, open_code=open_code)
        if file_info is None:
            return RGUIController.ui_render_template('VideoPreview.html')
        if file_info['type'] == 1:
            url = url_for('RGFileUpDown.play_list_share_page', open_code=open_code)
            return redirect(url)
        return RGUIController.ui_render_template('VideoPreview.html')
    except:
        return RGUIController.ui_render_template('VideoPreview.html')


@RestRouter.route('/nyapass/playList/sv<open_code>', methods=['GET'])
def play_list_share_page(open_code):
    return RGUIController.ui_render_template('VideoPreview.html')


"""
file
"""


@RestRouter.route('/fastUpload', methods=['POST'])
@RGUIController.auth_handler()
def new_user_file_with_hash(user_id):
    up_files = request_value(request, 'files')
    if up_files is None:
        return jsonify(form_res(RGResCode.lack_param))
    for file_key in up_files:
        file = up_files[file_key]
        file_type = int(file.get('type', 0))
        in_file = int(file.get('in_file', 0))

        if 'md5' not in file:
            if in_file:
                if file_type != 1:
                    return jsonify(form_res(RGResCode.lack_param))
            else:
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
    md5 = file.get('md5')
    in_album = file.get('in_album', False)
    album_id = file.get('album_id', None)
    in_file = file.get('in_file', 0)
    directory_id = file.get('directory_id', -1)
    file_type = file.get('type', 0)
    filename = file.get('name', '')

    if in_album:
        photo, code = pic.check_and_new_pic_with_hash(user_id=user_id, file_hash=md5, filename=filename,
                                                      album_id=album_id, full_url=False)
        file = {"file": photo, "code": code}
    elif in_file:
        # directory
        if int(file_type) == 1:
            file = files.new_directory(user_id=user_id, name=filename, directory_id=directory_id)
            code = RGResCode.ok if file is not None else RGResCode.insert_fail
        else:
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
            print(e)
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


@RestRouter.route('/upload', methods=['POST'])
@RGUIController.auth_handler()
def new_file(user_id):
    """
    上传文件
    body 参数:
        fileUpInfo      文件信息
        {file}          文件流
    """
    re_files = request.files
    file_up_info = request_value(request, 'fileUpInfo')
    if file_up_info is None:
        return jsonify(form_res(RGResCode.lack_param))
    file_up_info = json.loads(file_up_info, encoding="utf-8")

    for file_key in re_files:
        up_info = file_up_info.get(file_key, None)
        if up_info is None:
            return jsonify(form_res(RGResCode.lack_param))
        if up_info.get('md5', None) is None:
            return jsonify(form_res(RGResCode.lack_param))
        if up_info.get('in_file', 0):
            if not files.capacity_enough(user_id=user_id, new_file_size=request_file_size(request)):
                return jsonify(form_res(RGResCode.full_size))

    code, result = do_new_file()
    if code != RGResCode.ok:
        return jsonify(form_res(code))

    data = {}
    for up_res in result:
        file_key = up_res['key']

        up_info = file_up_info.get(file_key)
        set_name = up_info.get('name', '')

        in_album = up_info.get('in_album', 0)
        album_id = up_info.get('album_id', -1)

        in_file = up_info.get('in_file', 0)
        did = up_info.get('directory_id', -1)

        handle = handler_upload_res(user_id, up_res=up_res, set_name=set_name,
                                    in_album=in_album, album_id=album_id,
                                    in_file=in_file, directory_id=did)

        code = handle['code']
        data[file_key] = {
            'code': code,
            'file': handle['data'],
        }

        if code != RGResCode.ok and 'path' in up_res:
            del_filename = up_res['path']
            executor.submit(do_del_file, [del_filename])

    return jsonify(form_res(RGResCode.ok, data))


@RestRouter.route('/user/list', methods=['GET'])
@RGUIController.auth_handler()
def user_file_list(user_id):
    directory_id = request_value(request, 'directory_id', -1)
    try:
        result = files.user_file_list(user_id=user_id, directory_id=directory_id)
        return jsonify(form_res(RGResCode.ok, result))
    except:
        return jsonify(form_res(RGResCode.database_error))


@RestRouter.route('/user/playList', methods=['GET'])
@RGUIController.auth_handler()
def user_file_relative_list(user_id):
    code = request_value(request, 'code')
    if code is None:
        return jsonify(form_res(RGResCode.lack_param))
    u_id = None
    try:
        directory_id, u_id = RGRequestHelp.did_decode(code)
    except Exception as e:
        return jsonify(form_res(RGResCode.param_error))
    finally:
        if u_id != user_id:
            return jsonify(form_res(RGResCode.auth_fail))
    try:
        result, error = files.user_file_files_relative_with_id(user_id=user_id, id=directory_id)
        if error is not None:
            raise error
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
    user_file_id = request_value(request, 'id')
    if user_file_id is None:
        return jsonify(form_res(RGResCode.lack_param))

    args = {}
    personal_name = request_value(request, 'name')

    if personal_name is not None:
        args['personal_name'] = personal_name

    flag = files.user_file_set(user_id=user_id, id=user_file_id, args=args)
    if flag is True:
        code = RGResCode.ok
    else:
        code = RGResCode.update_fail
    return jsonify(form_res(code, None))


@RestRouter.route('/user/del', methods=['POST'])
@RGUIController.auth_handler()
def user_file_del(user_id):
    user_file_id = request_value(request, 'id')

    if user_file_id is None:
        return jsonify(form_res(RGResCode.lack_param))

    conn = None
    try:
        conn = dao.get()

        delete_files = files.user_file_del_and_return_files(user_id=user_id, id=user_file_id, conn=conn)

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
    user_file_id = request_value(request, 'id')
    if user_file_id is None:
        return jsonify(form_res(RGResCode.lack_param))

    to_id = request_value(request, 'to_id')
    if to_id is None:
        return jsonify(form_res(RGResCode.lack_param))
    flag = files.user_file_move(user_id=user_id, move_id=user_file_id, to_id=to_id)
    if flag is True:
        code = RGResCode.ok
    else:
        code = RGResCode.del_fail
    return jsonify(form_res(code, None))


@RestRouter.route('/user/fileSize', methods=['GET'])
@RGUIController.auth_handler()
def user_file_size(user_id):
    user_file_id = request_value(request, 'id', -1)
    if user_file_id is None:
        return jsonify(form_res(RGResCode.lack_param))

    user_file_id = int(user_file_id)
    error, file_size = files.user_file_size(user_id=user_id, id=user_file_id)
    if error is None:
        code = RGResCode.ok
    else:
        code = RGResCode.database_error
    return jsonify(form_res(code, {"size": file_size}))


@RestRouter.route('/user/fileInfo', methods=['GET'])
@RGUIController.auth_handler()
def user_file_info(user_id):
    file_id = request_value(request, 'id')
    if file_id is None:
        return jsonify(form_res(RGResCode.lack_param))

    info = files.user_file_info(user_id=user_id, id=file_id)
    if info is not None:
        del info['filename']
        code = RGResCode.ok
    else:
        code = RGResCode.database_error
    return jsonify(form_res(code, {"file": info}))


@RestRouter.route('/user/open/code', methods=['POST'])
@RGUIController.auth_handler()
def user_file_share_code(user_id):
    file_id = request_value(request, 'id')
    if file_id is None:
        return jsonify(form_res(RGResCode.lack_param))
    share_code = RGRequestHelp.fid_encode(file_id, user_id)
    flag = files.user_file_set(user_id=user_id, id=file_id, args={"open_code": share_code})
    if flag:
        code = RGResCode.ok
    else:
        share_code = None
        code = RGResCode.database_error
    return jsonify(form_res(code, {"shareCode": share_code}))


@RestRouter.route('/user/open/cancel', methods=['POST'])
@RGUIController.auth_handler()
def user_file_open_code_cancel(user_id):
    file_id = request_value(request, 'id')
    if file_id is None:
        return jsonify(form_res(RGResCode.lack_param))
    flag = files.user_file_set(user_id=user_id, id=file_id, args={"open_code": None})
    if flag:
        code = RGResCode.ok
    else:
        code = RGResCode.database_error
    return jsonify(form_res(code))


@RestRouter.route('/user/open/list', methods=['GET'])
@RGFileOpen.file_open_handler()
def user_file_open_list(**params):
    """
    根据 openCode 获取文件列表
    """
    result, error = files.user_file_files_relative_with_id(user_id=params['u_id'], id=params['f_id'], conn=params['conn'])
    if error is not None:
        raise error
    return jsonify(form_res(RGResCode.ok, result))


@RestRouter.route('/user/open/fileInfo', methods=['GET'])
@RGFileOpen.file_open_handler()
def user_file_open_file_info(**params):
    """
    根据 openCode 获取文件详情
    """
    info = params['info']
    del info['filename']
    return jsonify(form_res(RGResCode.ok, {'file': info}))


@RestRouter.route('/user/open/get', methods=['GET'])
@RGFileOpen.file_open_handler()
def user_file_open_file_get(**params):
    """
    根据openCode获取文件流
    """
    return __get_file_stream(params['info'])


@RestRouter.route('/user/open/get/<open_code>', methods=['GET'])
@RGFileOpen.file_open_handler(wrapper_code_key='open_code')
def user_file_open_file_url_get(**params):
    """
    根据openCode获取文件流
    """
    return __get_file_stream(params['info'])


def handler_upload_res(user_id, up_res, set_name=None,
                       in_album=False, album_id=-1, full_url=False,
                       in_file=False, directory_id=-1):
    """

    :param set_name:
    :param user_id: userId
    :param up_res: 上传结果
    :param in_album: 1代表存入相册 0代表不存入相册
    :param album_id: 插入到对应的相册
    :param in_file: 存入用户文件
    :param directory_id 文件夹id
    :param full_url: 返回全地址
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
        filename = ''
        if in_file and not files.capacity_enough(user_id=user_id, new_file_size=request_file_size(request), conn=conn):
            code = RGResCode.full_size
            raise Exception('capacity not enough')
        if 'flag' in up_res:
            if not up_res['flag']:
                code = RGResCode.server_error
                raise Exception(up_res['err_msg'])

            exif_info = None
            exif_time, size = 0, 0
            exif_gps_lalo, mime = '', ''

            if 'mime' in up_res:
                mime = up_res['mime']
            if 'name' in up_res:
                original_name = up_res['name']
            if 'size' in up_res:
                size = up_res['size']
            if 'path' in up_res:
                filename = up_res['path']
            if 'exif' in up_res:
                exif = up_res.get('exif', None)
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
                file_hash=up_res['hash'],
                exif_time=exif_time,
                exif_info=exif_info,
                exif_lalo=exif_gps_lalo,
                forever=0 if in_file else 1
            )
        if file_info is None:
            code = RGResCode.insert_fail
            raise Exception('new_file failed')

        if in_album and support_image(filename=filename):
            photo = pic.new_pic(user_id, file_info, album_id=album_id, conn=conn, title=original_name,
                                full_url=full_url)
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


@RestRouter.route('/user/get/<user_file_id>', methods=['GET'])
def user_file_get(user_file_id):
    if not is_int_number(user_file_id):
        return jsonify(form_res(RGResCode.lack_param))
    auth, user_id = RGUIController.do_auth()
    file = files.user_file_info(user_id=user_id, id=user_file_id, type=0)
    return __get_file_stream(file)


def __get_file_stream(file):
    filename = file['filename'] if file is not None and 'filename' in file else None
    mime = file['mime'] if file is not None and 'mime' in file else None
    name = file['name'] if file is not None and 'name' in file else None

    img_quality = request_value(request, 'img_quality', 'original')
    if img_quality == 'low':
        filename = name_fix(filename=filename, thumb=True, gif_activity=False)
    if filename is None:
        return jsonify(form_res(RGResCode.not_existed))
    return handle_download_file(filename, name, mime=mime)


@RestRouter.route('/<filename>', methods=['GET'])
def handle_download_file(filename, download_name=None, mime=None):
    range_mode = 'Range' in request.headers
    remote_url = handle_download_file_url(filename)
    params = {
        'mime': mime,
        'name': download_name,
        'cover': int(request_value(request, 'cover', 0))
    }
    req = requests.get(remote_url, headers=request.headers, json=params, stream=not range_mode)
    if req.status_code != 200 and req.status_code != 206:
        return Response(req.content, req.status_code, direct_passthrough=True)
    if range_mode:
        response = Response(req.content, 206, direct_passthrough=True)
    else:
        response = Response(stream_with_context(req.iter_content(chunk_size=2048)))
        if req.status_code == 200:
            response.headers['Cache-Control'] = 'max-age=604800'
    for key in req.headers:
        response.headers[key] = req.headers[key]
    return response


def handle_download_file_url(filename):
    return RemoteFileHost + '/' + FilePreFix + "download/" + filename


# 博客日志导入产生的图片存放的文件
@RestRouter.route('/import/<filename>', methods=['GET'])
def handle_download_import_file(filename):
    remote_url = RemoteFileHost + '/' + FilePreFix + "download/import/" + filename
    req = requests.get(remote_url, stream=True)
    content_type = req.headers['content-type']
    print(remote_url)
    return Response(stream_with_context(req.iter_content(chunk_size=1024)), content_type=content_type)


def do_new_file():
    """
    :return: code, [{name:'', success: True}, ……, ]
    """

    url = RemoteFileHost + '/' + FilePreFix + 'upload/'
    file_stream = {}

    re_files = request.files
    for file_key in re_files:
        stream = re_files[file_key]
        value = (stream.filename, stream.stream, stream.content_type)
        file_stream[file_key] = value

    # print('will upload')
    req = requests.post(url=url, files=file_stream, data=request.form, params=None,
                        auth=request.authorization, cookies=request.cookies, hooks=None, json=request.json, stream=True)
    # print('end upload status_code:%d' % req.status_code)

    if req.status_code == 200:
        t = req.json()
        return RGResCode.ok, t
    else:
        return RGResCode.server_error, None


def do_del_file(filenames):
    # print('will delete', filenames)
    url = RemoteFileHost + '/' + FilePreFix + 'del'
    req = requests.post(url=url, json={"names": filenames})
    # print('end delete status_code:%d' % req.status_code)


"""
decorator
"""


