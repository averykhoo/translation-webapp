let input_quill;
let output_quill;

document.addEventListener("DOMContentLoaded", function () {
    const $input_box = $('#translation_input');
    const $output_box = $('#translation_output');
    const $input_lang_option = $("input[name=input_language]");
    const $output_lang_option = $("input[name=output_language]");
    const $detected_language_notification = $("#detected_language_notification");
    const $translate_alert = $('#translating_alert');

    const $output_group_english = $('#output_english');
    const $output_lang_en = $('#output_en');
    const $output_group_other = $('#output_other');
    const $output_lang_zh = $('#output_zh');

    let xhr_detect = null;
    let xhr_translate = null;

    // settings for input quill
    let input_quill_options = {
        // debug: 'info',
        modules: {
            toolbar: quill_toolbar_options,
            table: false,
            'better-table': {
                operationMenu: {
                    color: {
                        colors: [
                            "rgba( 255 , 255 , 255 , 0.0 )",  // Transparent White
                            "black",
                            "red",
                            "yellow",
                            "green",
                            "blue",

                            // material palette
                            "rgba( 244 , 67  , 54  , 0.8 )",  // Red 500
                            "rgba( 233 , 30  , 99  , 0.8 )",  // Pink 500
                            "rgba( 156 , 39  , 176 , 0.8 )",  // Purple 500
                            "rgba( 103 , 58  , 183 , 0.8 )",  // Deep Purple 500
                            "rgba( 63  , 81  , 181 , 0.8 )",  // Indigo 500
                            "rgba( 33  , 150 , 243 , 0.8 )",  // Blue 500
                            // "rgba( 3   , 169 , 244 , 0.8 )",  // Light Blue 500
                            "rgba( 0   , 188 , 212 , 0.8 )",  // Cyan 500
                            "rgba( 0   , 150 , 136 , 0.8 )",  // Teal 500
                            "rgba( 76  , 175 , 80  , 0.8 )",  // Green 500
                            "rgba( 139 , 195 , 74  , 0.8 )",  // Light Green 500
                            "rgba( 205 , 220 , 57  , 0.8 )",  // Lime 500
                            "rgba( 255 , 235 , 59  , 0.8 )",  // Yellow 500
                            "rgba( 255 , 193 , 7   , 0.8 )",  // Amber 500
                            "rgba( 255 , 152 , 0   , 0.8 )",  // Orange 500
                            "rgba( 255 , 87  , 34  , 0.8 )",  // Deep Orange 500
                            "rgba( 121 , 85  , 72  , 0.8 )",  // Brown 500
                            "rgba( 158 , 158 , 158 , 0.8 )",  // Grey 500
                            "rgba( 96  , 125 , 139 , 0.8 )",  // Blue Grey 500
                        ],
                        text: 'Background Colors:'
                    },
                },
            },
            keyboard: {
                bindings: quillBetterTable.keyboardBindings
            },
            cursors: {
                transformOnTextChange: true,
            },
        },
        placeholder: 'Enter text',
        readOnly: false,
        theme: 'snow',

        // remove some formats from input quill
        formats: [
            'align',
            'background',
            'blockquote',
            'bold',
            'code',
            'code-block',
            'color',
            // 'direction',
            'font',
            // 'formula',
            'header',
            // 'image',
            'indent',
            'italic',
            // 'link',
            'list',
            'script',
            'size',
            'strike',
            'underline',
            // 'video'
        ],
    };

    // settings for the output quill
    let output_quill_options = {
        modules: {
            toolbar: false,
            table: false,
            'better-table': true,  // this somehow disables the right-click menu (possibly a bug, but it works)
            cursors: {
                transformOnTextChange: true,
            },
        },
        placeholder: 'Translation',
        readOnly: true,
        theme: 'snow',
    };


    const search_params = new URLSearchParams(window.location.search);

    input_quill = new Quill($input_box[0], input_quill_options);
    output_quill = new Quill($output_box[0], output_quill_options);

    let debounce_timeout = null;
    let last_detected = null;
    let last_translated = null;

    function reset_input_box() {
        // clear input
        input_quill.setContents(new Delta(), 'silent');

        // clear detected language notification
        $detected_language_notification.html("&nbsp;");

        // clear output (also resets font size)
        detect_language_and_translate();

        // clear hash
        update_hash();

        // clear timeout, erase all other variables
        clearTimeout(debounce_timeout);
        debounce_timeout = null;
        last_detected = null;
        last_translated = null;
    }

    function update_hash() {
        if (input_quill.getText().trim().length === 0) { // no input
            if (window.location.href !== mt_url) {
                window.history.pushState({}, mt_title, mt_url);
            }

        } else { // update url and hash, but don't pollute the history
            const new_href = mt_url + '#' + encodeURIComponent(input_quill.getSemanticHTML());
            let title_snippet = input_quill.getText().trim().replace(/\s+/gu, ' ');
            if (title_snippet.length > 50) {
                title_snippet = title_snippet.substr(0, 47) + '...';
            }
            title_snippet = ' [' + title_snippet + ']';
            title_snippet = title_snippet.substr(0, Math.min(50, title_snippet.length));
            if (new_href !== window.location.href) {
                window.history.pushState({state: new Date()}, null, new_href);
                document.title = mt_title + title_snippet;
            }
        }
    }

    function translate_and_set_output(text, html, input_lang_code, output_lang_code) { // put output into output box
        update_input_font_size();

        // don't re-translate
        if (input_lang_code + output_lang_code + html === last_translated) {
            return;
        } else {
            last_translated = input_lang_code + output_lang_code + html;
        }

        // re-translate, so abort previous translation (if any)
        if (xhr_translate !== null) {
            xhr_translate.abort();
            xhr_translate = null;
        }

        // no input
        if (input_quill.getText().trim().length === 0) {
            $translate_alert.hide();
            output_quill.setContents(new Delta(), 'silent');
            return
        }

        // longer than a tweet, let user know we're starting to translate since it could be slower
        if (html.length > 140) {
            $translate_alert.text("Translating...").show();
        }

        //run translation and populate the output box asynchronously
        xhr_translate = $.ajax({
            data: {
                input_lang: input_lang_code,
                output_lang: output_lang_code,
                input_html: html,
            },
            type: 'POST',
            url: '/translation/html',
        }).done(function (translated_html) {
            xhr_translate = null;
            const delta = output_quill.clipboard.convert({html: translated_html});
            output_quill.setContents(delta, 'silent');
            $translate_alert.hide();
        }).fail(function (jqXHR, text_status, error_thrown) {
            xhr_translate = null;
            if (jqXHR.status > 0) {
                const delta = output_quill.clipboard.convert({
                    html: '<pre><code>' + jqXHR.status + ' ' + jqXHR.statusText + '</code></pre>'
                });
                output_quill.setContents(delta, 'silent');
            }
        });
    }

    function set_output_languages(input_lang_code) { //update language pairs

        // if input is currently focused, refocus it after changing the lang
        const refocus_input = document.activeElement.className === "ql-editor";

        // what is the currently selected output lang
        const output_lang_code = $("input[name=output_language]:checked").val();

        let new_output_lang_code = output_lang_code;

        // english is incompatible with itself
        if (input_lang_code === "en" && output_lang_code === 'en') {
            $output_group_other.show();
            $output_group_english.hide();
            $output_lang_zh.click();
            new_output_lang_code = 'zh';
        }

        // non-english must go to english
        if (input_lang_code !== "en") {
            $output_group_english.show();
            $output_group_other.hide();
            $output_lang_en.click();
            new_output_lang_code = 'en';
        }

        if (refocus_input) {
            input_quill.focus();
        }

        return new_output_lang_code;
    }

    function update_input_font_size() {
        const len = input_quill.getText().length;
        const size_rem = 2.5 - Math.min(1.5, Math.max(0, ((len - 30) / 100)));
        $input_box.css('fontSize', size_rem.toString() + 'rem');
        $output_box.css('fontSize', size_rem.toString() + 'rem');
    }

    function detect_language_and_translate() {  // run translate right now

        // update hash
        update_hash();

        // clear debounce timer, if any
        clearTimeout(debounce_timeout);
        debounce_timeout = null;

        const content_html = input_quill.getSemanticHTML();
        const content_text = input_quill.getText();
        const input_lang_code = $("input[name=input_language]:checked").val();
        let output_lang_code = $("input[name=output_language]:checked").val();

        // don't re-translate
        if (input_lang_code + output_lang_code + content_html === last_detected && content_text.trim()) {
            return;
        } else {
            last_detected = input_lang_code + output_lang_code + content_html;
        }

        if (xhr_detect !== null) {
            xhr_detect.abort();
            xhr_detect = null;
        }

        // if lang is set to auto, detect the language and defer translate to async
        if (input_lang_code === 'auto' && content_text.trim()) {
            xhr_detect = $.ajax({
                data: {
                    input_text: content_text,
                },
                type: 'POST',
                url: '/translation/detect',
            }).done(function (lang_code) {
                xhr_detect = null;
                $detected_language_notification.html("Detected language as " + language_codes_mapping[lang_code]
                    + " (" + lang_code.toUpperCase() + ")"); // set notification
                output_lang_code = set_output_languages(lang_code);
                translate_and_set_output(content_text, content_html, lang_code, output_lang_code);
            });
        } else {
            // output language known, translate now
            $detected_language_notification.html("&nbsp;");  // clear notification
            output_lang_code = set_output_languages(input_lang_code);
            translate_and_set_output(content_text, content_html, input_lang_code, output_lang_code);
        }
    }

    function debounce_translate() {  // run translate, but only after at least half a second
        if (input_quill.getText().trim().length > 0) {
            if (debounce_timeout) {
                clearTimeout(debounce_timeout);
            } else {
                if (!output_quill.getText().trim().endsWith('...')) {
                    const delta = output_quill.clipboard.convert({
                        html: output_quill.getSemanticHTML() + "..."
                    });
                    output_quill.setContents(delta, 'silent');
                }
            }

            debounce_timeout = setTimeout(function () {
                detect_language_and_translate();
            }, 500)
        } else {
            detect_language_and_translate();
        }
    }

    function translate_hash() {
        const html = decodeURIComponent(window.location.hash.slice(1));
        reset_input_box();

        // set input based on fragment identifier
        if (html.trim().length > 0) {
            const delta = input_quill.clipboard.convert({html: html});
            input_quill.setContents(delta, 'user');
            detect_language_and_translate();
        }
        update_input_font_size();
        input_quill.focus();
    }


    $input_lang_option.on('change', function () {
        detect_language_and_translate();
    });

    $output_lang_option.on('change', function () { // if language is changed, retranslate immediately
        detect_language_and_translate();
    });

    input_quill.on('text-change', function () {  // user is currently editing (unless escape is pressed)
        update_input_font_size();
        if (input_quill.getText() === '\n') {
            reset_input_box();
        } else {
            debounce_translate();
        }
    });

    input_quill.on('selection-change', function (selection_range) {
        if (selection_range) {
            // not null means input_quill is focused
        } else {
            if (debounce_timeout) {
                detect_language_and_translate();
            }
        }
    });

    $input_box.on('keyup', function (keyup_event) {  // user is currently editing (unless escape is pressed)
        update_input_font_size();
        if (keyup_event.key === "Escape") {
            input_quill.blur();  // triggers instant_translate
        }
        if (keyup_event.key === "Enter") {
            detect_language_and_translate();
        }
    });

    $(window).on('keyup', function (keyup_event) {  // focus input on specific keys
        if (keyup_event.key === "Enter" || keyup_event.key === " ") {
            input_quill.focus();
        }
    });

    $(window).on('blur', function () {  // unfocus input box when you switch window (e.g. alt-tab)
        input_quill.blur();  // triggers instant_translate
    });

    // glow on focus
    $input_box.children().first()
        .focus(function () {
            $input_box.css('box-shadow', '0 0 0.5rem #007bff');
            $input_box.css('border-left', '1px solid transparent');
            $input_box.css('border-right', '1px solid transparent');
            $input_box.css('border-bottom', '1px solid transparent');
        })
        .focusout(function () {
            $input_box.css('box-shadow', '');
            $input_box.css('border', '');
        });

    // focus the input box
    input_quill.focus();

    // if we navigated here with some text input, translate the input
    translate_hash();
    window.addEventListener('hashchange', translate_hash);

});

