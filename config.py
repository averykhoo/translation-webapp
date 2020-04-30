import re
import socket
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
UPLOADS_DIR = PROJECT_DIR / 'uploads'
UPLOADS_DIR.mkdir(exist_ok=True, parents=True)
assert UPLOADS_DIR.is_dir(), UPLOADS_DIR
DOWNLOADS_DIR = PROJECT_DIR / 'downloads'
DOWNLOADS_DIR.mkdir(exist_ok=True, parents=True)
assert DOWNLOADS_DIR.is_dir(), DOWNLOADS_DIR

RE_WHITESPACE = re.compile(r'\s', flags=re.U)

MT_IP_ADDRESS = '0.0.0.0'
MT_PORT = 5000
MT_HOSTNAME = socket.gethostbyaddr(MT_IP_ADDRESS)[0].lower()  # I hope this works...
MT_URL = f'http://{MT_HOSTNAME}:{MT_PORT}'
MT_TEXT = f'{MT_URL}/app/text'
MT_TEXT_2 = f'{MT_URL}/app/dual'
MT_TEXT_XL = f'{MT_URL}/app/large'

APP_N_THREADS = 20  # browsers tend to send up to 6 requests per load, so n >= 6 prevents starvation
APP_SECRET_KEY = 'secret key'  # if you change this, all browser cookies get invalidated and reset
APP_DOMAINS = ['.eden.dot', '.dungeon.org', '.citadel.org']

BACKEND_IP_ADDRESS = '10.0.0.1'
BACKEND_API_KEY = '12345678-1234-1234-1234-123456789abc'

TRANSLATION_SIZE_LIMIT = 6 * 1024 * 1024  # up to 6 MiB, slightly larger than the file upload allows

LANGUAGE_CODES = {
    'en': 'English',
    'ms': 'Malay',
    'zh': 'Chinese (Simplified)',
    'id': 'Indonesian',
    'ar': 'Arabic',
    'vi': 'Vietnamese',
    'th': 'Thai',
}

with (PROJECT_DIR / 'bookmarklet_loader.js').open('rt', encoding='utf8') as f:
    BOOKMARKLET_LOADER_TEXT = f.read().replace('{MT_URL}', MT_URL).replace('{TARGET_URL}', MT_TEXT)
    BOOKMARKLET_LOADER_TEXT = re.sub(r'\s*[\r\n]\s*', ' ', BOOKMARKLET_LOADER_TEXT).strip()
    BOOKMARKLET_LOADER_TEXT = f'javascript:(function () {{ {BOOKMARKLET_LOADER_TEXT} }})();'

with (PROJECT_DIR / 'bookmarklet_loader.js').open('rt', encoding='utf8') as f:
    BOOKMARKLET_LOADER_2 = f.read().replace('{MT_URL}', MT_URL).replace('{TARGET_URL}', MT_TEXT_2)
    BOOKMARKLET_LOADER_2 = re.sub(r'\s*[\r\n]\s*', ' ', BOOKMARKLET_LOADER_2).strip()
    BOOKMARKLET_LOADER_2 = f'javascript:(function () {{ {BOOKMARKLET_LOADER_2} }})();'

with (PROJECT_DIR / 'bookmarklet_loader.js').open('rt', encoding='utf8') as f:
    BOOKMARKLET_LOADER_XL = f.read().replace('{MT_URL}', MT_URL).replace('{TARGET_URL}', MT_TEXT_XL)
    BOOKMARKLET_LOADER_XL = re.sub(r'\s*[\r\n]\s*', ' ', BOOKMARKLET_LOADER_XL).strip()
    BOOKMARKLET_LOADER_XL = f'javascript:(function () {{ {BOOKMARKLET_LOADER_XL} }})();'

with (PROJECT_DIR / 'bookmarklet_script.js').open('rt', encoding='utf8') as f:
    BOOKMARKLET_SCRIPT = f.read().replace('{MT_URL}', MT_URL)

SUPPORTED_FORMATS = {
    '.pdf':   ('application/pdf', '.docx'),

    '.bmp':   ('image/bmp', '.docx'),
    '.jpg':   ('image/jpeg', '.docx'),
    '.jpeg':  ('image/jpeg', '.docx'),
    '.png':   ('image/png', '.docx'),
    '.tif':   ('image/tiff', '.docx'),
    '.tiff':  ('image/tiff', '.docx'),

    '.doc':   (None, '.doc'),
    '.docx':  (None, '.docx'),
    '.pptx':  (None, '.pptx'),
    '.xlsx':  (None, '.xlsx'),

    '.odt':   (None, '.odt'),
    '.odp':   (None, '.odp'),
    '.ods':   (None, '.ods'),

    '.rtf':   ('text/rtf', '.rtf'),
    '.txt':   ('text/plain', '.txt'),
    '.htm':   ('text/html', '.html'),
    '.html':  ('text/html', '.html'),
    '.xhtml': ('application/xhtml+xml', '.xhtml'),
}

FORMAT_TO_IMAGE = {

    # compressed
    '.7z':    'compressed.svg',
    '.rar':   'compressed.svg',
    '.tgz':   'compressed.svg',
    '.gz':    'compressed.svg',
    '.tar':   'compressed.svg',
    '.bz2':   'compressed.svg',
    '.cab':   'compressed.svg',
    '.dmg':   'compressed.svg',
    '.sfx':   'compressed.svg',
    '.xz':    'compressed.svg',
    '.lz':    'compressed.svg',

    # document
    '.odm':   'doc.svg',
    '.doc':   'doc.svg',
    '.docx':  'doc.svg',
    '.docm':  'doc.svg',
    '.dot':   'doc.svg',
    '.dotm':  'doc.svg',
    '.dotx':  'doc.svg',
    '.docb':  'doc.svg',
    '.odt':   'doc.svg',
    '.ott':   'doc.svg',

    # excel
    '.xls':   'xls.svg',
    '.xlsx':  'xls.svg',
    '.xlt':   'xls.svg',
    '.xlm':   'xls.svg',
    '.xlsm':  'xls.svg',
    '.xltx':  'xls.svg',
    '.xltm':  'xls.svg',
    '.xlsb':  'xls.svg',
    '.xla':   'xls.svg',
    '.xlam':  'xls.svg',
    '.xlw':   'xls.svg',
    '.ods':   'xls.svg',
    '.ots':   'xls.svg',

    # powerpoint
    '.ppt':   'ppt.svg',
    '.pptx':  'ppt.svg',
    '.pot':   'ppt.svg',
    '.pps':   'ppt.svg',
    '.pptm':  'ppt.svg',
    '.potx':  'ppt.svg',
    '.potm':  'ppt.svg',
    '.ppam':  'ppt.svg',
    '.ppsx':  'ppt.svg',
    '.ppsm':  'ppt.svg',
    '.sldx':  'ppt.svg',
    '.sldm':  'ppt.svg',
    '.odp':   'ppt.svg',
    '.otp':   'ppt.svg',

    # executable
    '.exe':   'exe.svg',
    '.bat':   'exe.svg',
    '.cmd':   'exe.svg',
    '.sh':    'exe.svg',
    '.ps1':   'exe.svg',

    # pdf
    '.pdf':   'pdf.svg',
    '.ps':    'pdf.svg',
    '.eps':   'pdf.svg',

    # adobe
    '.ai':    'ai.svg',
    '.dwg':   'dwg.svg',
    '.fla':   'fla.svg',
    '.psd':   'psd.svg',

    '.avi':   'avi.svg',
    '.jpeg':  'jpg.svg',
    '.jpg':   'jpg.svg',
    '.mp3':   'mp3.svg',
    '.mp4':   'mp4.svg',
    '.png':   'png.svg',
    '.svg':   'svg.svg',

    # text-based
    '.css':   'css.svg',
    '.csv':   'csv.svg',
    '.tsv':   'csv.svg',
    '.htm':   'html.svg',
    '.html':  'html.svg',
    '.xhtml': 'html.svg',
    '.js':    'js.svg',
    '.json':  'json.svg',
    '.rtf':   'rtf.svg',
    '.txt':   'txt.svg',
    '.md':    'txt.svg',
    '.xml':   'xml.svg',

    # others
    '.dbf':   'dbf.svg',
    '.iso':   'iso.svg',
    '.zip':   'zip.svg',
    '.zipx':  'zip.svg',

    # not files
    # 'file':   'file.svg',
    # 'search': 'search.svg',
}
