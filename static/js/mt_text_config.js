let Delta;

const mt_url = window.location.href.slice(0, -(window.location.search + window.location.hash).length);
const mt_title = 'Machine Translation';

Delta = Quill.import('delta');
const Clipboard = Quill.import('modules/clipboard');


// replica ql-clipboard that fixes some paste bugs
class FixedClipboard extends Clipboard {
    onPaste(selection_range, {text, html}) {  // override existing onPaste to fix the bugs

        // fix html (sometimes broken when pasting from Word into Chrome)
        const fixed_html = html.slice(0, html.search(new RegExp('</html>', 'imu'))) + '</html>';
        const current_format = this.quill.getFormat(selection_range.index);

        // convert html / text to a delta, trying to retain the formatting of the current selection
        let pasted_delta = this.quill.clipboard.convert({html: fixed_html, text: text}, current_format);

        // don't break tables if pasting into a table cell (based on #33 in quill-better-tables)
        const [line] = this.quill.getLine(selection_range.index);
        if (line && line.constructor.name === 'TableCellLine') {

            // loop over each op in the delta to build a new delta
            pasted_delta = pasted_delta.reduce((new_delta, op) => {
                if (op.insert && typeof op.insert === 'string') {

                    // don't allow code-blocks in cells
                    let op_format = $.extend({}, op.attributes);
                    if (op_format['code-block']) {
                        op_format['code'] = op_format['code-block'];
                        delete op_format['code-block'];
                    }

                    // convert to unix line endings
                    let string_to_insert = op.insert.replace(new RegExp('\\r+\\n?'), '\n');

                    // insert all newlines separately so we don't break the table schema
                    let start = 0;
                    for (let i = 0; i < string_to_insert.length; i++) {
                        if (string_to_insert.charAt(i) === '\n') {
                            new_delta.insert(string_to_insert.substring(start, i), op_format);
                            new_delta.insert('\n', $.extend({}, op_format, line.formats()));
                            start = i + 1;
                        }
                    }

                    // op to insert remainder
                    if (string_to_insert.substring(start)) {
                        new_delta.insert(string_to_insert.substring(start), op_format);
                    }
                } else {
                    // not text (e.g. image)
                    new_delta.insert(op.insert, op.attributes)
                }

                // this is the fixed delta
                return new_delta
            }, new Delta());
        }

        // apply the paste at the cursor, replacing any selected content
        const update_delta = new Delta()
            .retain(selection_range.index)
            .delete(selection_range.length)
            .concat(pasted_delta);

        // apply the change
        this.quill.updateContents(update_delta, 'user');

        // selection_range.length contributes to delta.length(), so subtract it away before moving the cursor
        this.quill.setSelection(update_delta.length() - selection_range.length, 'silent');
        this.quill.scrollIntoView();
    };
}


Quill.register({
    'modules/better-table': quillBetterTable,
    'modules/clipboard': FixedClipboard,
    'modules/cursors': QuillCursors,
}, true);


// setup input quill toolbar
const quill_toolbar_options = [
    // [{'font': []}, {'size': []}],  // font, size, color
    // [{ 'header': [1, 2, 3, 4, 5, 6, false] }],

    // ['bold', 'italic', 'underline', 'strike', 'code'],    // formatting
    [{'header': 1}, {'header': 2}],                          // header shortcuts
    [{'align': []}],

    [{'list': 'ordered'}, {'list': 'bullet'}],
    [{'indent': '-1'}, {'indent': '+1'}],                    // outdent/indent
    // [{'script': 'super'}, {'script': 'sub'}],             // superscript/subscript
    // [{ 'direction': 'rtl' }],                             // text direction
    [{'color': []}, {'background': []}],                     // font/bg colors

    // ['link', 'image', 'video', 'formula'],
    // ['blockquote', 'code-block'],                         // quoting

    ['clean'],                                               // remove formatting button
];
