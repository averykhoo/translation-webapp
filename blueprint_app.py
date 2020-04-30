from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

import config
from utils import get_session

blueprint = Blueprint('mt_web_app', __name__)


@blueprint.route('/')
def web_app_home():
    return redirect(url_for('.web_app_text'))


@blueprint.route('/duo')
def web_app_text_duo():
    return redirect(url_for('.web_app_text_dual'))


@blueprint.route('/xl')
def web_app_text_xl():
    return redirect(url_for('.web_app_text_large'))


@blueprint.route('/text')
def web_app_text():
    user_session = get_session(current_app, session, request)
    return render_template('mt_text.html',
                           bookmarklet=config.BOOKMARKLET_LOADER_TEXT,
                           username=user_session['username'])


@blueprint.route('/dual')
def web_app_text_dual():
    user_session = get_session(current_app, session, request)
    return render_template('mt_text_dual.html',
                           bookmarklet=config.BOOKMARKLET_LOADER_2,
                           username=user_session['username'])


@blueprint.route('/large')
def web_app_text_large():
    user_session = get_session(current_app, session, request)
    return render_template('mt_text_large.html',
                           bookmarklet=config.BOOKMARKLET_LOADER_XL,
                           username=user_session['username'])


@blueprint.route('/file')
def web_app_file():
    user_session = get_session(current_app, session, request)
    return render_template('mt_file.html',
                           bookmarklet='',
                           username=user_session['username'])
