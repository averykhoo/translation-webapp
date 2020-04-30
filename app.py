import datetime
from threading import Lock

import waitress
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import request
from flask import send_from_directory
from flask import session
from flask import url_for

import blueprint_app
import blueprint_translation
import blueprint_utils
import config

app = Flask(__name__)
app.secret_key = config.APP_SECRET_KEY
app.server_init = datetime.datetime.now().isoformat()
app.server_sessions = []
app.session_append_lock = Lock()
app.counter = 0

app.mt_files = dict()
app.mt_in_progress = dict()

app.register_blueprint(blueprint_app.blueprint, url_prefix='/app')
app.register_blueprint(blueprint_utils.blueprint, url_prefix='/utils')
app.register_blueprint(blueprint_translation.blueprint, url_prefix='/translation')


@app.before_request
def before_request():
    # ensure session exists
    blueprint_utils.get_session(app, session, request)

    session.permanent = True
    session.modified = True
    # pprint(blueprint_utils.request_info(app, session, request))


@app.route('/')
def home():
    return redirect(url_for('web_app'))


@app.route('/app')
def web_app():
    return redirect(url_for('mt_web_app.mt_text'))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'img/translator-icon-3.jpg')


@app.route('/bookmarklet_script')
def bookmarklet_script():
    return config.BOOKMARKLET_SCRIPT


@app.route('/hello')
def hello_world():
    return jsonify('hello world')


@app.route('/hello/<name>')
def hello_name(name):
    return f'<h1>Hello, {name}!</h1>'


if __name__ == '__main__':
    waitress.serve(app,
                   host=config.MT_IP_ADDRESS,
                   port=config.MT_PORT,
                   threads=config.APP_N_THREADS,
                   )
