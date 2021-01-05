from RGUtil.RGCodeUtil import RGResCode
import magic


def get_data_with_request(_request):
    if _request.is_json:
        return _request.json
    return _request.values
    # if _request.method == "POST":
    #     return _request.form
    # elif _request.json:
    #     return _request.json
    # return _request.args


def request_value(_request, key, default=None):
    args = get_data_with_request(_request)
    if key in args:
        return args[key]
    else:
        return default


def request_ip(_request, default=None):
    headers = _request.headers
    if 'X-Real-Ip' in headers:
        return headers['X-Real-Ip']
    else:
        return default


def form_res(code, data=None):
    if code == 0:
        code = RGResCode.not_existed if data is None else RGResCode.ok

    if data is not None:
        if not isinstance(data, dict) and not isinstance(data, list):
            data = data.__dict__
        res = {
            'code': int(code),
            'data': data
        }
        return res
    else:
        res = {
            'code': int(code),
        }
        return res


def is_int_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


def request_file_size(request):
    re_files = request.files
    size = 0
    for file_key in re_files:
        file = re_files[file_key]
        file.seek(0)
        size += len(file.read())
        file.seek(0)
    return size


def request_file_mine(request):
    re_files = request.files
    size = 0
    for file_key in re_files:
        file = re_files[file_key]
        file.seek(0)
        size += len(file.read())
        file.seek(0)
    return size
