from functools import wraps

from flask import session, request, jsonify, make_response, redirect, url_for, json, render_template

from Model import tokens
from RGIgnoreConfig.RGGlobalConfigContext import RGJSVersion, RGCSSVersion
from RGUtil.RGCodeUtil import RGResCode
from RGUtil.RGRequestHelp import get_data_with_request, request_value, is_int_number, form_res


class RGUIController(object):
    pass


def auth_handler(page=False, forceLogin=True, more_info=False, need_email=False):
    """

    Decorator for session or token valid required.
    """

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if more_info:
                    auth, user_id, email, username = do_auth_more_info(need_request_email=need_email)
                    params = {
                        'auth': auth,
                        'user_id': user_id,
                        'email': email,
                        'username': username,
                    }
                else:
                    auth, user_id = do_auth()
                    params = user_id

                t = get_data_with_request(request)
                logs = json.dumps(t, sort_keys=True, indent=4, separators=(', ', ': '))
                print('auth_handler -->\n{}\nuserid:{}\n{}\n'.format(request.path, user_id, logs))

                if forceLogin:
                    if auth:
                        return func(params, *args, **kwargs)
                    else:

                        return make_response(jsonify({'error': 'Unauthorized access'}), 401) \
                            if not page else redirect(request.full_path.replace(request.path, url_for('login_page')))
                else:
                    return func(params, *args, **kwargs)
            except Exception as ex:
                print(ex)
                token_session_remove()
                return make_response(jsonify({'error': 'System Error'}), 500)
                # return make_response(jsonify({'error': 'System Error'}), 500) \
                #     if page is False else redirect(url_for('login_page'))

        return wrapper

    return decorator


def check_bind():
    """

    Decorator for session or token valid required.
    """

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:

                t = get_data_with_request(request)
                logs = json.dumps(t, sort_keys=True, indent=4, separators=(', ', ': '))
                print('check_bind -->\n{}\n{}\n'.format(request.path, logs))

                if user_need_to_bind_page():
                    return redirect(url_for('bind_page'))
                return func(*args, **kwargs)
            except Exception as ex:
                print(ex)
                return func(*args, **kwargs)
        return wrapper

    return decorator


def do_auth():
    auth, user_id, email, username = do_auth_more_info(need_request_email=False)
    return auth, user_id


def do_auth_more_info(need_request_email=False):
    user_id = None
    auth = False
    email = None
    username = None
    if 'token' in session and 'type' in session and session['type'] == 0 and session['token'] is not None:
        if 'user_id' in session:
            user_id = session['user_id']
            email = session['email'] if 'email' in session else None
            username = session['username'] if 'username' in session else None

            if need_request_email or username is None:
                from Model import user
                _user = user.get_user(user_id=user_id, need_bg=False, need_email=need_request_email)
                if username is None:
                    session['username'] = _user.username
                    username = _user.username
                if need_request_email:
                    session['email'] = _user.email
                    email = _user.email

            auth = True
    elif 'auth' in request.headers:
        token = request.headers.get('auth')
        user_id, auth = tokens.certify_token(token)
    return auth, user_id, email, username


def user_need_to_bind_page():
    auth, user_id, email, username = do_auth_more_info(need_request_email=False)
    if auth:
        if (email is None or len(email) <= 0) and username is not None:
            try:
                from User import RGOpenIdController
                from RGUtil.RGCodeUtil import RGResCode
                code, data = RGOpenIdController.user_list(username=username)
                if code == RGResCode.ok and len(data) > 0:
                    session['email'] = data[0]['email']
                    return False
                else:
                    return True
            except Exception as e:
                print('user_need_to_bind_page')
                print(e)
                return False
    return False


def token_session(uid=None, token_type=None, username=None, email=None, remember=None):
    # c = requests.cookies.RequestsCookieJar()
    # c.set('cookie-token', token, path='/')
    # sessions.cookies.update(c)
    session['user_id'] = uid
    session['username'] = username
    session['email'] = email
    token = tokens.generate_token_ifneed(uid, token_type)
    session['token'] = token
    session['type'] = token_type
    if remember is not None:
        session.permanent = True if remember is not None and remember > 0 else False
    return token


def token_session_remove():
    session.pop('user_id', '')
    session.pop('username', '')
    session.pop('email', '')
    session.pop('token', '')
    session.pop('type', '')
    session.permanent = False


def ui_render_template(template_name_or_list, **context):

    art_user_id = request_value(request, 'user_id', None)
    need_user = int(request_value(request, 'needUserInfo', 0))

    if need_user > 0 and (art_user_id is None or is_int_number(art_user_id) is False):
        return jsonify(form_res(RGResCode.lack_param))

    params = dict({"js_ver": RGJSVersion, "css_ver": RGCSSVersion}, **context)
    render = render_template(template_name_or_list, **params)

    if need_user > 0:
        from Model import user
        auth, view_user_id = do_auth()
        relation = user.get_relation(view_user_id, art_user_id)
        re_relation = user.get_relation(art_user_id, view_user_id)
        t = {
            "user": user.get_user(art_user_id).__dict__,
            "home": user.isHome(view_user_id, art_user_id),
            "auth": view_user_id is not None,
            "relation": relation,
            "re_relation": re_relation,
            'render': render
        }
        return jsonify(form_res(RGResCode.ok, t))
    return render


# def authorizeRequireWarp(fn):
#     """
#     Decorator for session valid required.
#     """
#
#     @wraps(fn)
#     def wrapper(self, session, *args, **kwargs):
#         try:
#             if RGSessionManager.check(session) is True:
#                 return fn(self, session, *args, **kwargs)
#             else:
#                 return False, RGUIController.unauthorized(session)
#         except Exception as e:
#             print "Exception in COrgan: %s" % str(e)
#             return False, e
#
#     return wrapper
#
#
# @staticmethod
# def unauthorized(session):
#     """
#     Warp unauthorized service request feedback package.
#     :param session: session id
#     :return: unauthorized feedback
#     """
#     try:
#         sObj = RGSessionManager.GetSession(session)
#         sUser = ""
#         if sObj is not None:
#             sUser = sObj.Username
#         RGLogUtil.Log("username:%s, session:%s unauthorized request." % (sUser, session),
#                     RGUIController.__name__, "Warning", True)
#     except Exception as e:
#         print "Exception in RenWebUI authorization check: %s" % str(e)
#     finally:
#         return GCC.UNAUTHORIZED
