from datetime import timedelta

from flask import Flask, send_file, redirect, url_for
from flask.sessions import SecureCookieSessionInterface, SecureCookieSession

import RGUIController
from Blog import RGBlogApp
from Files import RGFileUpDownApp
from Photos import RGPhotoApp
from RGIgnoreConfig.RGGlobalConfigContext import RGHost, RGPort, RGDebug
from RGUtil.RGCodeUtil import RGVerifyType
from User import RGUserApp


class CacheSecureCookieSession(SecureCookieSession):
    removeVaryCookie = False


class CacheSessionInterface(SecureCookieSessionInterface):
    session_class = CacheSecureCookieSession

    def open_session(self, app, request):
        session = super().open_session(app, request)
        return session

    def save_session(self, app, session, response):
        super().save_session(app, session, response)
        if session.removeVaryCookie == True:
            if response.vary.find('Cookie') >= 0:
                response.vary.remove('Cookie')


app = Flask(__name__, template_folder='templates', static_folder='static')
app.session_interface = CacheSessionInterface()
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

app.config['SECRET_KEY'] = 'niang_pa_si'
# app.config['REMEMBER_COOKIE_DURATION'] = timedelta(minutes=5)

app.register_blueprint(RGFileUpDownApp.RestRouter)
app.register_blueprint(RGBlogApp.RestRouter)
app.register_blueprint(RGUserApp.RestRouter)
app.register_blueprint(RGPhotoApp.RestRouter)


app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=15)


@app.route('/favicon.ico', methods=['GET'])
def favicon():
    return send_file("RGIgnoreConfig/favicon.ico", mimetype='image/ico', cache_timeout=0)


@app.route('/apple-touch-icon.png', methods=['GET'])
@app.route('/apple-touch-icon-precomposed.png', methods=['GET'])
def apple_icon():
    try:
        auth, user_id = RGUIController.do_auth()
        if auth is True:
            from Model import user
            filename = user.get_user_icon_name(user_id)
            if filename:
                return RGFileUpDownApp.handle_download_file(filename=filename)

        return send_file("RGIgnoreConfig/apple-icon.png", mimetype='image/png', cache_timeout=0)
    except:
        return send_file("RGIgnoreConfig/apple-icon.png", mimetype='image/png', cache_timeout=0)


"""
page
"""


@app.route('/', methods=["GET"])
@RGUIController.auth_handler(page=True)
def home_page(user_id):
    if user_id is None:
        return redirect(url_for('login_page'))
    else:
        return redirect(url_for('RGBlog.auto_blog_page'))


@app.route('/bindPage', methods=["GET"])
def bind_page():
    if not RGUIController.user_need_to_bind_page():
        return redirect(url_for('login_page'))
    auth, user_id, email, username = RGUIController.do_auth_more_info(need_request_email=False)
    return RGUIController.ui_render_template("login.html", **{
        'username': username,
        'coll_email': True,
        'verify_type': RGVerifyType.bind
    })


@app.route('/loginPage', methods=["GET"])
def login_page():
    try:
        auth, user_id = RGUIController.do_auth()
        if auth is False:
            return RGUIController.ui_render_template("login.html")
        else:
            return redirect(url_for('RGBlog.auto_blog_page'))
    except:
        return RGUIController.ui_render_template("login.html")


if __name__ == '__main__':
    # app.debug = True
    app.config['JSON_AS_ASCII'] = False
    app.run(host=RGHost, port=RGPort, debug=RGDebug, threaded=True, processes=1)
