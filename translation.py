import os
import warnings
from pathlib import Path
from typing import Optional
from typing import Union

import cld2
import cld2full
import requests
from langid import langid

import config
from utils import clean_text

langid_identifier = langid.LanguageIdentifier.from_modelstring(langid.model, norm_probs=True)
langid_identifier.set_languages(config.LANGUAGE_CODES.keys())


def langid_cld2full(text: str):
    is_reliable, bytes_found, details = cld2full.detect(text)

    if not is_reliable:
        return None

    for language_name, language_code, percent, score in details:
        if language_code not in config.LANGUAGE_CODES:
            continue

        if score < 500:
            return None

        if percent < 30:
            return None

        return language_code

    return None


def langid_cld2(text: str):
    is_reliable, bytes_found, details = cld2.detect(text)

    if not is_reliable:
        return None

    for language_name, language_code, percent, score in details:
        if language_code not in config.LANGUAGE_CODES:
            continue

        if score < 1000:
            return None

        if percent < 50:
            return None

        return language_code

    return None


def langid_api_call(text: str, timeout_seconds: Optional[Union[float, int]] = None):
    if timeout_seconds is None:
        timeout_seconds = max(1, len(text) // 5000)
    try:
        r = requests.post(f'http://{config.BACKEND_IP_ADDRESS}:8903/detect/language',
                          timeout=timeout_seconds,
                          data={
                              'key':   config.BACKEND_API_KEY,
                              'input': text[:10000],
                          })
    except requests.Timeout:
        return None, -2

    output = r.json()['outputs'][0]
    language_code_extended = output['detectedLanguage']
    confidence = output['detectedLanguageConfidence']
    language_code = language_code_extended[:2]

    if language_code not in config.LANGUAGE_CODES:
        return None, -1

    return language_code, confidence


def language_detect(text: str) -> Optional[str]:
    # cleanup
    text = clean_text(text)

    # no text input
    if not text:
        return None

    # hard-code in this one case
    if text.lower() == 'assalamualaikum':
        return 'ms'

    # first, try cld2full (most accurate)
    try:
        language_code = langid_cld2full(text)
        if language_code:
            return language_code
    except ValueError:
        pass

    # second, try cld2 (less accurate)
    try:
        language_code = langid_cld2(text)
        if language_code:
            return language_code
    except ValueError:
        pass

    # use api_call's langid
    sys_language, sys_score = langid_api_call(text)
    sys_score *= 0.8  # backend system tends to be overconfident even when wrong

    # last, fallback to langid (constrained to ALWAYS produce an answer)
    language_code, score = langid_identifier.classify(text)

    if sys_score * 3 / 4 > score:
        return sys_language

    return language_code


def translate_api_call_plaintext(input_lang: str, output_lang: str, input_text: str) -> Optional[str]:
    # cleanup
    input_text = clean_text(input_text)

    # clean languages
    input_lang = input_lang.lower().strip()
    output_lang = output_lang.lower().strip()

    # langid
    if input_lang == 'auto':
        input_lang = language_detect(input_text)

    # sanity checks
    if input_lang not in config.LANGUAGE_CODES:
        warnings.warn(f'unexpected source language = {input_lang}')
    if output_lang not in config.LANGUAGE_CODES:
        warnings.warn(f'unexpected target language = {output_lang}')

    # same language, no need api call
    if input_lang == output_lang:
        return input_text

    # run translation
    r = requests.post(f'http://{config.BACKEND_IP_ADDRESS}:8903/translation/text/translate',
                      data={
                          'key':    config.BACKEND_API_KEY,
                          'source': input_lang,
                          'target': output_lang,
                          'input':  input_text,
                      })
    return r.json()['outputs'][0]['output']


def translate_api_call_html(input_lang: str, output_lang: str, input_html: str) -> Optional[str]:
    # cleanup
    input_html = clean_text(input_html)

    # clean languages
    input_lang = input_lang.lower().strip()
    output_lang = output_lang.lower().strip()

    # no langid because it's html, please check the plaintext language instead

    # sanity checks
    if input_lang not in config.LANGUAGE_CODES:
        warnings.warn(f'unexpected source language = {input_lang}')
    if output_lang not in config.LANGUAGE_CODES:
        warnings.warn(f'unexpected target language = {output_lang}')

    # same language, no need api call
    if input_lang == output_lang:
        return input_html

    # run translation
    r = requests.post(f'http://{config.BACKEND_IP_ADDRESS}:8903/translation/file/translate',
                      data={
                          'key':    config.BACKEND_API_KEY,
                          'source': input_lang,
                          'target': output_lang,
                          'input':  input_html,
                          'format': 'html',
                      })

    result = r.text.lstrip()
    if result.startswith('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n'):
        result = result[68:]
    else:
        warnings.warn(f'html did not start with expected header! {repr(result)[:100]}')
    return result


def _translate_api_call_file_request(input_lang: str,
                                     output_lang: str,
                                     input_path: Union[os.PathLike, str],
                                     file_format: Optional[str],
                                     translate_async: bool,
                                     ) -> Optional[requests.Response]:
    # cleanup
    input_path = Path(os.path.abspath(input_path))

    # impose size limit
    if input_path.stat().st_size > config.TRANSLATION_SIZE_LIMIT:
        return None

    # translate params
    data = {'key':    config.BACKEND_API_KEY,
            'source': input_lang,
            'target': output_lang,
            }

    # translate async
    if translate_async:
        data['async'] = True

    # if format is specified
    if file_format is not None:
        data['format'] = file_format

    # translate file
    with input_path.open('rb') as f:
        r = requests.post(f'http://{config.BACKEND_IP_ADDRESS}:8903/translation/file/translate',
                          data=data, files={'input': f})

        # api_call gives back the request id
        if r.status_code == 200:
            return r


def translate_api_call_file_blocking(input_lang: str,
                                     output_lang: str,
                                     input_path: Union[os.PathLike, str],
                                     output_path: Union[os.PathLike, str],
                                     file_format=None,
                                     ) -> Optional[Path]:
    # cleanup
    output_path = Path(os.path.abspath(output_path))

    # translate
    r = _translate_api_call_file_request(input_lang=input_lang,
                                         output_lang=output_lang,
                                         input_path=input_path,
                                         file_format=file_format,
                                         translate_async=False)

    # save file
    if r is not None:
        with output_path.open('wb') as f:
            f.write(r.content)

        # return path
        return output_path


def translate_api_call_file_async(input_lang: str,
                                  output_lang: str,
                                  input_path: Union[os.PathLike, str],
                                  file_format: str = None,
                                  ) -> Optional[str]:
    # translate
    r = _translate_api_call_file_request(input_lang=input_lang,
                                         output_lang=output_lang,
                                         input_path=input_path,
                                         file_format=file_format,
                                         translate_async=True)

    # api_call gives back the request id
    if r is not None:
        return r.json()['requestId']


def translate_api_call_file_status(request_id: str) -> Optional[str]:
    r = requests.post(f'http://{config.BACKEND_IP_ADDRESS}:8903/translation/file/status',
                      data={
                          'key':       config.BACKEND_API_KEY,
                          'requestId': request_id,
                      })

    # api_call gives back the request id
    if r.status_code == 200:
        status = r.json()['status']
        if status not in {'registered',
                          'import',
                          'started',
                          'pending',
                          'export',
                          'finished',
                          'error'
                          }:
            warnings.warn(r.json())

        return status


def translate_api_call_file_cancel(request_id: str) -> Optional[str]:
    r = requests.post(f'http://{config.BACKEND_IP_ADDRESS}:8903/translation/file/cancel',
                      data={
                          'key':       config.BACKEND_API_KEY,
                          'requestId': request_id,
                      })

    if r.status_code == 200:
        return translate_api_call_file_status(request_id)


def translate_api_call_file_result(request_id: str, output_path: Union[os.PathLike, str]) -> Optional[Path]:
    # cleanup
    output_path = Path(os.path.abspath(output_path))

    # check
    if translate_api_call_file_status(request_id) != 'finished':
        return

    # get file
    r = requests.post(f'http://{config.BACKEND_IP_ADDRESS}:8903/translation/file/result',
                      data={
                          'key':       config.BACKEND_API_KEY,
                          'requestId': request_id,
                      })

    # save output
    if r.status_code == 200:
        with output_path.open('wb') as f:
            f.write(r.content)

        # return path
        return output_path
