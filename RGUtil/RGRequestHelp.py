from RGUtil.RGCodeUtil import http_code


def get_data_with_request(_request):
    if _request.method == "POST":
        return _request.form
    else:
        return _request.args


def form_res(code, data):
    if code == 0:
        code = http_code.not_existed if data is None else http_code.ok

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
