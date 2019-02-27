from datetime import timedelta

from flask import Flask, render_template, send_file, redirect, url_for

import RGUIController
from Blog import RGBlogApp
from Files import RGFileUpDownApp
from Photos import RGPhotoApp
from RGGlobalConfigContext import RGHost, RGPort
from User import RGUserApp

app = Flask(__name__, template_folder='templates', static_folder='static')
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

app.config['SECRET_KEY'] = 'niang_pa_si'
# app.config['REMEMBER_COOKIE_DURATION'] = timedelta(minutes=5)

app.register_blueprint(RGFileUpDownApp.RestRouter)
app.register_blueprint(RGBlogApp.RestRouter)
app.register_blueprint(RGUserApp.RestRouter)
app.register_blueprint(RGPhotoApp.RestRouter)


# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)


@app.route('/favicon.ico', methods=['GET'])
def favicon():
    return send_file("favicon.ico", mimetype='image/ico', cache_timeout=0)


@app.route('/apple-touch-icon.png', methods=['GET'])
@app.route('/apple-touch-icon-precomposed.png', methods=['GET'])
def apple_icon():
    try:
        auth, user_id = RGUIController.do_auth()
        if auth is True:
            from Model import user
            filename = user.get_user_iconname(user_id)
            if filename:
                return RGFileUpDownApp.handle_download_file(filename=filename)

        return send_file("apple-icon.png", mimetype='image/png', cache_timeout=0)
    except:
        return send_file("apple-icon.png", mimetype='image/png', cache_timeout=0)


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


@app.route('/loginPage', methods=["GET"])
def login_page():
    try:
        auth, user_id = RGUIController.do_auth()
        if auth is False:
            return render_template("login.html")
        else:
            return redirect(url_for('RGBlog.auto_blog_page'))
    except:
        return render_template("login.html")


if __name__ == '__main__':
    # app.debug = True
    app.config['JSON_AS_ASCII'] = False
    app.run(host=RGHost, port=RGPort)
