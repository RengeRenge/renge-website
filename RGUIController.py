from functools import wraps

from flask import session, request, jsonify, make_response, redirect, url_for, json, render_template

from Model import tokens
from RGIgnoreConfig.RGGlobalConfigContext import RGJSVersion, RGCSSVersion
from RGUtil.RGRequestHelp import get_data_with_request


class RGUIController(object):
    pass


def auth_handler(page=False, forceLogin=True):
    """

    Decorator for session or token valid required.
    """

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                auth, user_id = do_auth()
                if auth:
                    if user_need_to_bind_page() and page is True:
                        return redirect(url_for('bind_page'))

                if forceLogin:
                    if auth:
                        return func(user_id, *args, **kwargs)
                    else:
                        return make_response(jsonify({'error': 'Unauthorized access'}), 401) \
                            if not page else redirect(url_for('login_page'))
                else:
                    return func(user_id, *args, **kwargs)
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
                if user_need_to_bind_page():
                    return redirect(url_for('bind_page'))
                return func(*args, **kwargs)
            except Exception as ex:
                print(ex)
                return func(*args, **kwargs)
        return wrapper

    return decorator


def do_auth():
    auth, user_id, email, username = do_auth_more_info()
    return auth, user_id


def do_auth_more_info():
    user_id = None
    auth = False
    email = None
    username = None
    if 'token' in session and 'type' in session and session['type'] == 0 and session['token'] is not None:
        if 'user_id' in session:
            user_id = session['user_id']
            email = session['email'] if 'email' in session else None
            username = session['username'] if 'username' in session else None
            auth = True

            t = get_data_with_request(request)
            params = json.dumps(t, sort_keys=True, indent=4, separators=(', ', ': '))
            print('>>>>\nauth:{}\nuserid:{}\n{}\n<<<<'.format(request.path, user_id, params))
    elif 'auth' in request.headers:
        token = request.headers.get('auth')
        user_id, auth = tokens.certify_token(token)
    return auth, user_id, email, username


def user_need_to_bind_page():
    auth, user_id, email, username = do_auth_more_info()
    if auth:
        if email is None or len(email) <= 0:
            try:
                from User import RGOpenIdController
                from RGUtil.RGCodeUtil import RGResCode
                code, data = RGOpenIdController.user_list(username=username)
                if code == RGResCode.ok and len(data) > 0:
                    return False
            except:
                pass
            return True
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
    del session['user_id']
    del session['username']
    del session['email']
    del session['token']
    del session['type']
    session.permanent = False


def ui_render_template(template_name_or_list, **context):
    params = dict({"js_ver": RGJSVersion, "css_ver": RGCSSVersion}, **context)
    return render_template(template_name_or_list, **params)


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
