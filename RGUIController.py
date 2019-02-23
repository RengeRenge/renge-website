from functools import wraps

from flask import session, request, jsonify, make_response, redirect, url_for

from Model import tokens


class RGUIController(object):
    pass


def auth_handler(page=False):
    """

    Decorator for session or token valid required.
    """

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                auth, user_id = do_auth()
                if auth:
                    return func(user_id, *args, **kwargs)
                else:
                    return make_response(jsonify({'error': 'Unauthorized access'}), 401) \
                        if page is False else redirect(url_for('login_page'))
            except Exception as ex:
                print(ex)
                return make_response(jsonify({'error': 'System Error'}), 500)
                # return make_response(jsonify({'error': 'System Error'}), 500) \
                #     if page is False else redirect(url_for('login_page'))

        return wrapper

    return decorator


def do_auth():
    if 'token' in session and 'type' in session and session['type'] is 0:
        if 'user_id' in session:
            user_id = session['user_id']
            auth = True
        else:
            user_id = None
            auth = False
    else:
        token = request.headers.get('auth')
        user_id, auth = tokens.certify_token(token)
    return auth, user_id

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
