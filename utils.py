import datetime
import hashlib
import os
import socket
import warnings
from typing import Iterable
from typing import Tuple
from typing import Union

import ftfy
# noinspection PyProtectedMember
from bs4 import UnicodeDammit

import config


def ensure_unicode(text: str, most_likely_encodings: Union[str, Iterable[str], None] = None) -> str:
    if isinstance(most_likely_encodings, str):
        most_likely_encodings = [most_likely_encodings]
    elif most_likely_encodings is None:
        most_likely_encodings = []

    # decode bytes
    if isinstance(text, (bytes, bytearray)):
        text = UnicodeDammit.detwingle(text)

    # unexpected type, just coerce
    elif not isinstance(text, str):
        text = str(text)

    # convert to unicode
    text = UnicodeDammit(text, most_likely_encodings).unicode_markup

    # ftfy for good measure
    return ftfy.fix_text(text)


def get_session(flask_app, flask_session, flask_request, ignore_existing=False):
    if flask_session.get('server_init', None) == flask_app.server_init:
        if not ignore_existing:
            return flask_app.server_sessions[flask_session['idx']]

    try:
        hostname, alias_list, ip_addr_list = socket.gethostbyaddr(flask_request.remote_addr)
        username = hostname
        for domain in config.APP_DOMAINS:
            if username.endswith(domain):
                username = username[:-len(domain)]
    except socket.herror:
        hostname = None
        alias_list = []
        ip_addr_list = [flask_request.remote_addr]
        username = None

    with flask_app.session_append_lock:
        flask_session['server_init'] = flask_app.server_init
        flask_session['idx'] = len(flask_app.server_sessions)
        new_server_session = {
            'idx':          flask_session['idx'],
            'addr':         flask_request.remote_addr,
            'hostname':     hostname,
            'alias_list':   alias_list,
            'ip_addr_list': ip_addr_list,
            'username':     username,
            'created':      datetime.datetime.now().isoformat(),
        }
        flask_app.server_sessions.append(new_server_session)
        return new_server_session


def request_info(flask_app, flask_session, flask_request):
    # convert to dict so it can be serialized to json
    _session = dict()
    _session.update(flask_session)

    return {
        'remote_addr':    flask_request.remote_addr,

        'flask_session':  _session,
        'server_session': get_session(flask_app, flask_session, flask_request),

        'method':         flask_request.method,
        'url':            flask_request.url,
        'files':          flask_request.files,
        'form':           flask_request.form,
        'query':          flask_request.args,
        'server_init':    flask_app.server_init,
    }


UPLOADED_FILE_INFO_HEADERS = ['path',
                              'filename',
                              'extension',
                              'size',
                              'sha256',
                              'md5',
                              'created',
                              ]


def split_filename(filename: Union[os.PathLike, str]) -> Tuple[str, str]:
    extension_max_len = 6  # arbitrary, but must fit '.docx'

    # split into filename and extension
    filename, extension = ensure_unicode(os.path.basename(filename)).rsplit('.', 1)
    extension = '.' + extension.strip().lower()

    # suffixes to allow
    _suffixes = {
        '.gz',
        '.bz2',
        '.lz',
        '.lzma',
        '.lzo',
        '.xz',
        '.z',
        '.zst',
    }
    _suffixes.update([f'.{i:03d}' for i in range(100)])  # .001, .002, ..., .099

    # special handling for known suffix
    extension_suffix = ''
    if extension in _suffixes and '.' in filename[-extension_max_len:]:
        extension_suffix = extension
        filename, extension = filename.rsplit('.', 1)
        extension = '.' + extension.strip().lower()

    # fix extensions
    if len(extension) > extension_max_len:
        extension = '.unknown'
    elif extension == '.htm':  # normalize to html
        extension = '.html'
    elif extension == '.jpeg':  # normalize to jpg
        extension = '.jpg'

    # replace extension suffix
    extension += extension_suffix

    return filename.strip(), extension


def save_uploaded_file(flask_request):
    if 'file' not in flask_request.files:
        return dict.fromkeys(UPLOADED_FILE_INFO_HEADERS, None)

    # read data but retain position in file
    current_pos = flask_request.files['file'].tell()
    flask_request.files['file'].seek(0)
    binary_data = flask_request.files['file'].read()
    flask_request.files['file'].seek(current_pos)

    if len(binary_data) == 0:
        return dict.fromkeys(UPLOADED_FILE_INFO_HEADERS, None)

    # hash data
    sha256_hash = hashlib.sha256(binary_data).hexdigest()
    md5_hash = hashlib.md5(binary_data).hexdigest()

    # create filename based on sha256 hash and file extension
    orig_name, extension = split_filename(flask_request.files['file'].filename)
    new_filename = sha256_hash + extension
    path = config.UPLOADS_DIR / new_filename

    # save file
    created = None
    if path.is_file():
        if path.stat().st_size != len(binary_data):
            warnings.warn(f'duplicate non-matching file! ({path})')
    elif path.is_dir():
        warnings.warn(f'path is dir! ({path})')
    else:
        with path.open('wb') as f:
            f.write(binary_data)
        created = datetime.datetime.now().isoformat()

    # return some info
    return {
        'path':      str(path),
        'orig_name': orig_name,
        'filename':  new_filename,
        'extension': extension,
        'size':      len(binary_data),
        'sha256':    sha256_hash,
        'md5':       md5_hash,
        'created':   created,
    }


def clean_text(text: str, max_encoded_length: int = config.TRANSLATION_SIZE_LIMIT) -> str:
    # cleanup
    text = ensure_unicode(text.strip())

    # no text input
    if not text:
        return ''

    # impose length limit on ENCODED text
    truncated_length = max_encoded_length
    min_length = 0
    while len(text[:truncated_length].encode('utf8')) > max_encoded_length:
        delta_length = (truncated_length - min_length) // 2
        if delta_length == 0:
            truncated_length -= 1
            break

        # bisect the length until we find the right spot
        if len(text[:min_length + delta_length].encode('utf8')) > max_encoded_length:
            truncated_length = min_length + delta_length
        else:
            min_length = min_length + delta_length

    # if text has to be truncated, keep going back until we see whitespace (search the last 1% of the text)
    if truncated_length < len(text):
        for i in range(truncated_length // 100):
            if config.RE_WHITESPACE.fullmatch(text[truncated_length - i]) is not None:
                text = text[:truncated_length - i]
                break

        # no whitespace found, just truncate
        else:
            text = text[:truncated_length]

    return text.strip()
