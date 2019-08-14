# encoding: utf-8
import uuid

import requests
from flask import request

from RGIgnoreConfig.RGGlobalConfigContext import RGPublicHost
from RGUtil import RGTimeUtil
from RGUtil.RGCodeUtil import RGResCode
from RGUtil.RGRequestHelp import request_value

CTOpenIdUserApi = "http://127.0.0.1:20721/api/user"
CTOpenIdUserAuthApi = "http://127.0.0.1:20721/api/sauth"


def user_list(username=None, email=None):
    # username = json.dumps(username)
    params = {}
    if username:
        params = openid_base_params({
            'usernames': [username]
        })
    elif email:
        params = openid_base_params({
            'emails': [email]
        })

    req = requests.get(
        url=CTOpenIdUserApi,
        json=params
    )
    t = req.json()
    print(t)

    data = None
    code = RGResCode.server_error
    if 'code' in t and t['code'] == 200:
        code = RGResCode.ok
        data = t['data']
    return code, data


def user_data(username=None, email=None):
    # username = json.dumps(username)
    code, data = user_list(username=username, email=email)
    if code == RGResCode.ok and len(data) > 0:
        return data[0]
    else:
        return None


def user_new(username, email, password):
    if username is None:
        return RGResCode.lack_param, None
    if email is None:
        return RGResCode.lack_param, None
    if password is None:
        return RGResCode.lack_param, None

    print('new user with open id u:[%s] e:[%s]' % (username, email))

    req = requests.post(
        url=CTOpenIdUserApi,
        json=openid_base_params({
            'username': username,
            'email': email,
            'pwd': password,
        })
    )
    t = req.json()
    print(t)

    code = RGResCode.server_error
    if 'code' in t and t['code'] == 200:
        code = RGResCode.ok if t['sub_code'] == 0 else RGResCode.insert_fail
    return code


def user_update(username, password=None, payload=None):
    if username is None:
        return RGResCode.lack_param, None

    params = openid_base_params({'username': username})
    if password:
        params['pwd'] = password
    if payload:
        params['extra_payload'] = password
    req = requests.put(
        url=CTOpenIdUserApi,
        json=params
    )
    t = req.json()
    print(t)

    code = RGResCode.server_error
    if 'code' in t and t['code'] == 200:
        code = RGResCode.ok if t['sub_code'] == 0 else RGResCode.update_fail
    return code


def user_delete(username):
    if username is None:
        return RGResCode.lack_param, None

    params = openid_base_params({'usernames': [username]})
    req = requests.delete(
        url=CTOpenIdUserApi,
        json=params
    )
    t = req.json()
    print(t)

    code = RGResCode.server_error
    data = None
    if 'code' in t and t['code'] == 200:
        code = RGResCode.ok
        data = t['data']
    return code, data


def auth(username, password):
    req = requests.post(
        url=CTOpenIdUserAuthApi,
        json=openid_base_params({
            'username': username,
            'pwd': password
        })
    )
    t = req.json()
    print(t)
    data = None
    code = RGResCode.server_error
    if 'code' in t and t['code'] == 200:
        data = t['data']
        code = RGResCode.ok if t['sub_code'] == 0 else RGResCode.auth_fail
    return code, data


def openid_base_params(extra=None):
    # 登录验证, 注册新用户, 更新用户信息
    # token 保留字段;
    # username 用户名;
    # pwd 密码;
    # appid 来自何种应用的注册请求;
    # clientId 用户设备唯一号;
    # timestamp 注册请求到达应用的时间戳;
    # login_channel 用户渠道标识符; iOS pc android
    # extra_payload 保留字典字段;
    # user_ip 客户端ip;
    # remote_ip 服务端ip；
    params = {
        # 'token': '',
        # 'username': username,
        # 'email': email,
        # 'pwd': password,
        'request_id': str(uuid.uuid1()),
        'appid': 'RGBlog',
        'clientId': request_value(request, 'clientId', default=''),
        'timestamp': RGTimeUtil.timestamp(),
        'login_channel': request_value(request, 'channel', default=''),
        # 'extra_payload': '用户名',
        'user_ip': request_value(request, 'ip', default=''),
        'remote_ip': RGPublicHost
    }
    if extra is not None:
        params = dict(params, **extra)
    return params
