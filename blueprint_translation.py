import json
from pathlib import Path

import requests
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request
from flask import send_from_directory
from flask import session
from werkzeug.utils import secure_filename

import config
from translation import language_detect
from translation import translate_api_call_file_async
from translation import translate_api_call_file_cancel
from translation import translate_api_call_file_result
from translation import translate_api_call_file_status
from translation import translate_api_call_html
from translation import translate_api_call_plaintext
from utils import get_session
from utils import save_uploaded_file

blueprint = Blueprint('mt_translation', __name__)


@blueprint.route('/detect', methods=['POST'])
def detect_language():
    return language_detect(text=request.form['input_text'])


@blueprint.route('/text', methods=['POST'])
def translate_plaintext():
    return translate_api_call_plaintext(input_lang=request.form['input_lang'],
                                        output_lang=request.form['output_lang'],
                                        input_text=request.form['input_text'])


@blueprint.route('/html', methods=['POST'])
def translate_html():
    return translate_api_call_html(input_lang=request.form['input_lang'],
                                   output_lang=request.form['output_lang'],
                                   input_html=request.form['input_html'])


@blueprint.route('/icon/<filename>')
def icon(filename):
    """
    this must be a GET request because we're just going to use this as the src in an <img> tag
    """

    # this stupid thumbs.db is really irritating sometimes
    if filename.lower().strip() == 'thumbs.db':
        return send_from_directory('static', 'img/poop.png')
    elif '.' not in filename:
        return send_from_directory('static', 'img/filetypes/file.svg')
    else:
        extension = '.' + filename.rsplit('.', 1)[-1].lower()
        return send_from_directory('static', f'img/filetypes/{config.FORMAT_TO_IMAGE.get(extension, "file.svg")}')


@blueprint.route('/upload', methods=['POST'])
def upload():
    headers = ['uuid',
               'filename',
               'last_modified',
               'last_modified_date',
               'size',
               'type',
               'input_lang',
               'output_lang',
               'md5_hash',
               'md5_elapsed',
               'added',
               'removed',
               ]

    # you MUST have a uuid
    if 'uuid' not in request.form:
        return jsonify(False)

    # in case the uuid isn't unique (e.g. same random seed, or user re-using uuid between sessions)
    session_info = get_session(current_app, session, request)
    unique_id = (session_info['idx'], request.form['uuid'])

    # where to save info
    file_info = current_app.mt_files.setdefault(unique_id, dict())
    file_info.setdefault('browser', dict())
    file_info.setdefault('server', dict())

    # save browser metadata
    for header in headers:
        if header in request.form:
            file_info['browser'][header] = request.form[header]  # overwrite existing

    # if file translation is in progress but file is removed, try to cancel translation
    if file_info['browser'].get('removed', False):
        if file_info.get('output_path', None) in current_app.mt_in_progress:
            request_id = current_app.mt_in_progress[file_info['output_path']]
            if translate_api_call_file_cancel(request_id) is not None:
                del current_app.mt_in_progress[file_info['output_path']]

    # no uploaded file, so nothing left to do
    if 'file' not in request.files:
        return jsonify(False)

    # file already uploaded
    if 'path' in file_info['server']:
        return jsonify(False)

    # save file locally
    file_info['server'].update(save_uploaded_file(request))
    if file_info['server']['path'] is None:  # file could not be saved
        file_info['server'].clear()
        return jsonify(False)

    # create output filename
    file_info['format'], file_info['output_extension'] = config.SUPPORTED_FORMATS[file_info['server']['extension']]
    output_filename = file_info['server']['orig_name']
    if language_detect(output_filename) == file_info['browser']['input_lang']:
        output_filename = translate_api_call_plaintext(file_info['browser']['input_lang'],
                                                       file_info['browser']['output_lang'],
                                                       file_info['server']['orig_name'])
    file_info['output_filename'] = secure_filename(output_filename + file_info['output_extension'])

    # language checks
    input_lang = file_info['browser']['input_lang'].lower()
    output_lang = file_info['browser']['output_lang'].lower()
    assert input_lang in config.LANGUAGE_CODES, input_lang
    assert output_lang in config.LANGUAGE_CODES, output_lang
    file_info['input_lang'] = input_lang
    file_info['output_lang'] = output_lang

    # where to put output file
    input_path = file_info['server']['path']
    output_filename = file_info['server']['sha256'] + file_info['output_extension']
    output_path = config.DOWNLOADS_DIR / f'{input_lang}-{output_lang}' / output_filename
    output_path.parent.mkdir(exist_ok=True, parents=True)
    assert output_path.parent.is_dir(), output_path.parent
    file_info['input_path'] = str(input_path)
    file_info['output_path'] = str(output_path)

    # translation complete or in progress
    if output_path.is_file() or file_info['output_path'] in current_app.mt_in_progress:
        return jsonify(True)

    # translate file
    request_id = translate_api_call_file_async(input_lang, output_lang, input_path, file_format=file_info['format'])
    file_info['request_id'] = request_id
    current_app.mt_in_progress[file_info['output_path']] = request_id
    return jsonify(True)


@blueprint.route('/status', methods=['POST'])
def status():
    # you MUST have a uuid
    if 'uuid' not in request.form:
        return jsonify(False)

    # in case the uuid isn't unique (e.g. same random seed, or user re-using uuid between sessions)
    session_info = get_session(current_app, session, request)
    unique_id = (session_info['idx'], request.form['uuid'])

    # invalid uuid / session
    if unique_id not in current_app.mt_files:
        return jsonify(False)
    file_info = current_app.mt_files[unique_id]

    # is translation complete
    output_path = Path(file_info['output_path'])
    if output_path.exists():
        if file_info['output_path'] in current_app.mt_in_progress:
            del current_app.mt_in_progress[file_info['output_path']]
        return jsonify({'link_url':    f'/translation/download/{request.form["uuid"]}',
                        'link_name':   file_info['output_filename'],
                        'link_text':   'Download',
                        'status_text': f'File translation complete!<br>'
                                       f'Output: <em>{file_info["output_filename"]}</em>',
                        })

    # get status (and pull file if finished)
    elif file_info['output_path'] in current_app.mt_in_progress:
        request_id = current_app.mt_in_progress[file_info['output_path']]
        translation_status = translate_api_call_file_status(request_id)

        # if finished, download in background
        if translation_status == 'finished':
            translate_api_call_file_result(request_id, file_info['output_path'])

        # if error, remove from processing queue
        elif translation_status == 'error':
            del current_app.mt_in_progress[file_info['output_path']]

        # show status (and spinner)
        return jsonify({'link_url':    None,
                        'link_name':   None,
                        'link_text':   None,
                        'status_text': f'Translating file... ({translation_status})',
                        })

    # translation has failed (removed from queue without output)
    else:
        return jsonify({'link_url':    f'/translation/download/{request.form["uuid"]}',
                        'link_name':   'error.log',
                        'link_text':   'Error',
                        'status_text': 'File translation failed :(',
                        })


@blueprint.route('/download/<uuid>')
def download(uuid):
    """
    this must be a GET request because we're just going to use this as the href in an <a> tag
    """
    # in case the uuid isn't unique (e.g. same random seed, or user re-using uuid between sessions)
    session_info = get_session(current_app, session, request)
    unique_id = (session_info['idx'], uuid)

    # invalid uuid / session
    if unique_id not in current_app.mt_files:
        return False
    file_info = current_app.mt_files[unique_id]

    # send file if exists
    output_path = Path(file_info['output_path'])
    if output_path.exists():
        return send_from_directory(str(output_path.parent), output_path.name)

    # send error log
    return jsonify(file_info)
