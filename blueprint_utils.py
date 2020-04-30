from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request
from flask import session

import config
from utils import get_session
from utils import request_info

blueprint = Blueprint('mt_utils', __name__)


@blueprint.route('/echo', methods=['GET', 'POST'])
def echo():
    return jsonify(request_info(current_app, session, request))


@blueprint.route('/whoami')
def whoami():
    return jsonify({'ip':         request.remote_addr,
                    'session_id': session['idx'],
                    'username':   get_session(current_app, session, request)['username'],
                    })


@blueprint.route('/counter')
def counter():
    current_app.counter += 1

    session_info = get_session(current_app, session, request)
    session_info.setdefault('counter', 0)
    session_info['counter'] += 1

    session.setdefault('counter', 0)
    session['counter'] += 1

    return jsonify({'user':    session_info['counter'],
                    'global':  current_app.counter,
                    'browser': session['counter'],
                    })


@blueprint.route('/config')
def print_config():
    return jsonify({key: val if isinstance(val, (str, int, float, list, dict)) else str(val)
                    for key, val in config.__dict__.items()
                    if key.isupper()})


@blueprint.route('/sessions')
def print_sessions():
    return jsonify(current_app.server_sessions)


@blueprint.route('/session')
def print_session():
    return jsonify(get_session(current_app, session, request))


@blueprint.route('/new_session')
def new_session():
    return jsonify(get_session(current_app, session, request, ignore_existing=True))
