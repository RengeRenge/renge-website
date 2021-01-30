import base64
import random
import time

from RGUtil.RGCodeUtil import RGResCode


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


baseList = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjklmnopqrstuvwxyz'


def encode(n, b=58):
    """

    :param n: 压缩的数字
    :param b: 进制 最大58
    :return: 对应进制字符串
    """
    result = ''
    x = int(n)
    while True:
        x, y = divmod(x, b)
        result = baseList[y] + result
        if x <= 0:
            break
    return result


def decode(n, b=58):
    """

    :param n: 数字压缩后的字符串
    :param b: 对应的进制 最大58
    :return: 原来的数字
    """
    result = 0
    length = len(n)
    for index in range(length):
        result += (baseList.index(n[index]) * pow(b, length - index - 1))
    return result


def did_encode(dir_id, uid):
    dir_id = int(dir_id) + 10
    dir_id = str(dir_id)
    count = 0

    # if len(dir_id) < 8:
    #     count = 8 - len(dir_id)
    #     dir_id = ''.join(['0', '0', '0', '0', '0', '0', '0', '0'][:count]) + dir_id

    count = str(count)

    uid = encode(uid)
    dir_id = encode(dir_id)

    content = '{}{}.{}.{}'.format(dir_id, uid, count, len(str(uid)))
    return safe_encode_b64(content, random_index=0)


def did_decode(content):
    content = safe_decode_b64(content)
    contents = content.split(sep='.')

    uid_count = int(contents[-1])
    count = int(contents[-2])

    content = contents[0]
    uid = content[-uid_count:]
    dir_id = content[:-uid_count]
    dir_id = dir_id[count:]
    return int(decode(dir_id)) - 10, int(decode(uid))


def fid_encode(f_id, uid):
    f_id = int(f_id) + 10
    time_str = str((time.time_ns()//1000) % 10000000)
    f_id = '{}{}'.format(f_id, time_str)
    f_id = encode(int(f_id))
    return safe_encode_b64('{}.{}.{}'.format(f_id, uid, len(time_str)))


def fid_decode(content):
    content = safe_decode_b64(content)
    contents = content.split(sep='.')
    length = int(contents[-1])
    uid = contents[-2]
    f_id = str(decode(contents[0]))
    f_id = f_id[0:-length]
    return int(f_id) - 10, uid


def safe_encode_b64(content, random_index=None):
    content = base64.urlsafe_b64encode(content.encode("utf-8"))
    content = str(content, "utf-8")
    del_count = 0
    for i in range(len(content) - 1, -1, -1):
        if content[i] == '=':
            del_count += 1
            content = content[:-1]
        else:
            break
    if random_index is None:
        index = random.randint(0, len(content) - 1)
    else:
        index = 0
    return encode(index) + content[:index] + encode(del_count) + content[index:]


def safe_decode_b64(content):
    index = decode(content[0])
    content = content[1:]
    del_count = decode(content[index])
    content = content[:index] + content[index+1:]
    for i in range(del_count):
        content += '='
    return str(base64.urlsafe_b64decode(content.encode("utf-8")), "utf-8")


def bytes_to_hex_string(bytes):
    result = ''
    for byte in bytes:
        result += '%02X' % byte
    return result


def hex_string_to_bytes(hex_string):
    byte_array = bytearray()
    for index in range(len(hex_string) // 2):
        temp = hex_string[2 * index:2 * index + 2]
        temp = bytes(temp, encoding='utf-8')
        temp = int(temp, base=16)
        byte_array.append(temp)
    return byte_array


if __name__ == '__main__':
    code = encode(1000, 58)
    print('#58', code)
    print('#10', decode(code, 58))

    dir_id = 122134
    uid = 9812312332
    print('did', dir_id, 'user_id', uid)
    code = did_encode(dir_id=dir_id, uid=uid)
    print('did_encode', code)
    did, user_id = did_decode(code)
    print('did', did, 'user_id', user_id)

    token = fid_encode(f_id=dir_id, uid=uid)
    print('fid_encode', token)
    did, user_id = fid_decode(token)
    print('did', did, 'user_id', user_id)
