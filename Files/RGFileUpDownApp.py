# encoding: utf-8

import requests
from flask import Blueprint, request, jsonify, stream_with_context, Response

import RGUIController
from Files.RGFileGlobalConfigContext import RemoteFileHost, FilePreFix
from Model import files, pic
from RGUtil.RGCodeUtil import http_code
from RGUtil.RGRequestHelp import get_data_with_request, form_res

RestRouter = Blueprint('RGFileUpDown', __name__, url_prefix='/' + FilePreFix)

"""
file
"""


@RestRouter.route('/upload/', methods=['POST'])
@RGUIController.auth_handler()
def new_file(user_id):
    """

    :param user_id: userId
    :return: response, [{name:'', success: True}, ……, ]
    """
    t = get_data_with_request(request)

    bool
    simditor = False
    if 'simditor' in t:
        simditor = True

    url = RemoteFileHost + '/' + FilePreFix + 'upload/'
    file_stream = {}

    re_files = request.files
    for name in re_files:
        stream = re_files[name]
        value = (stream.filename, stream.stream, stream.content_type)
        file_stream[name] = value
    # file_stream = request.files['file']
    # file_stream = {
    #     file_stream.name: (file_stream.filename, file_stream.stream, file_stream.content_type),
    # }
    print('will upload')
    req = requests.post(url=url, files=file_stream, data=request.form, params=None,
                        auth=request.authorization, cookies=request.cookies, hooks=None, json=request.json, stream=True)

    t = req.json()
    print('end upload')
    if simditor:
        return handler_upload_res(user_id, t[0], simditor=True)
    else:
        data = {}
        for res in t:
            flag, file_info = handler_upload_res(user_id, res)
            file_key = res['key']
            data[file_key] = {
                'success': flag,
                'file': file_info,
            }
        return jsonify(form_res(http_code.ok, data))


def handler_upload_res(user_id, t, simditor=False):
    """

    :param user_id: userId
    :param t: 上传结果
    :param simditor: simditor 富文本编辑器
    :return: 如果是simditor, 返回对应的response， 其他则返回 flag 和 RGFile的__dict__
    """
    file_info = None
    if 'err_msg' in t:
        err_msg = t['err_msg']
        if len(err_msg) <= 0:
            if 'type' in t:
                file_type = t['type']
            if 'name' in t:
                name = t['name']
            if 'path' in t:
                file_name = t['path']
            if 'exif' in t:
                exif = t['exif']

            file_info = files.new_file(file_name, file_type, exif)

    if file_info is not None and file_info.ID >= 0:

        if str(file_info.type).startswith('image/') and simditor:
            _pic = pic.new_pic(user_id, file_info, title=name, needFullUrl=not simditor)

        if simditor is True:

            if _pic:
                res_data = {
                    "success": True,
                    "file_path": _pic.url,
                }
            else:
                res_data = {
                    "success": False,
                }
            return jsonify(res_data)

        else:
            return True, file_info.__dict__
    else:
        if simditor is True:
            res_data = {
                "success": False,
                "msg": err_msg,
                "file_path": "",
            }
            return jsonify(res_data)
        else:
            return False, None
            # res = form_res(http_code.insert_fail, None)
            # return jsonify(res)


@RestRouter.route('/<filename>', methods=['GET'])
def handle_download_file(filename):
    remote_url = RemoteFileHost + '/' + FilePreFix + "download/" + filename
    req = requests.get(remote_url, stream=True)
    content_type = req.headers['content-type']
    print (remote_url)
    return Response(stream_with_context(req.iter_content(chunk_size=1024)), content_type=content_type)
