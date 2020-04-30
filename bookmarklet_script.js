function bookmarklet_run(TARGET_URL) {
    // this is dynamically loaded
    // this is because we will need to change bookmarklet functionality
    // but we don't want to have to instruct all the users to update their bookmarklets
    // another good thing is that since this is a real .js script, we can have comments

    // this will be where we're going
    let mt_url = '{MT_URL}/app/text'.toLowerCase();
    if (TARGET_URL) {
        mt_url = TARGET_URL.toLowerCase();
    }

    // where are we now, and what has the user selected?
    const current_url = window.location.href.toString();
    const selected_text = window.getSelection().toString();

    // if we're in a mt app, don't discard any existing query string or hash text (yet)
    let params;
    let fragment_identifier = '';
    if (current_url.trim().toLowerCase().startsWith('{MT_URL}/app/')) {
        params = new URLSearchParams(window.location.search);
        fragment_identifier = window.location.hash
    } else {
        params = new URLSearchParams();
    }

    // also give the text source URL
    params.set('previous_url', encodeURIComponent(current_url));

    // create target URL
    let target_url = mt_url + '?' + params.toString();

    // if any text was selected, add that to the fragment identifier because there's no length limit there
    if (selected_text.trim()) {
        fragment_identifier = '#' + encodeURIComponent(selected_text);
    }

    // add the text to be translated, if any
    target_url = target_url + fragment_identifier;

    // if we're already in the correct MT app tab, we don't need to create a new window
    if (current_url.trim().toLowerCase().startsWith(mt_url)) {

        // input_quill should be global, so just replace the text as user, the text-change event should handle the rest
        if (typeof input_quill !== 'undefined') {
            const delta = input_quill.clipboard.convert({text: selected_text});
            input_quill.setContents(delta, 'user');
            window.getSelection().empty();
            return;
        }

        // can't find quill, bookmarklet may be outdated, navigate current tab instead
        console.log('unable to find input_quill!');
        window.location.href = target_url;
        return;
    }

    // avoid re-using any other tab by creating a probably-unique title
    const today = new Date();
    const new_tab_title = 'Machine Translation' + ' ' + today.toISOString();

    // create a new tab and focus that tab
    const new_tab = window.open(target_url, new_tab_title);

    // new tab successfully created, focus that tab
    if (new_tab) {
        new_tab.focus && new_tab.focus();
    } else {

        // new tab blocked, ask if they want to navigate current tab
        if (confirm('Unable to open new tab, pop-ups may be blocked. ' +
            'Please disable your pop-up blocker and restart your browser. ' +
            'For now, do you want to open translation in this tab?')) {
            window.location.href = target_url;
        } else {

            // user chose not to navigate, tell them how to enable popups
            console.log('user chose to do nothing, showing instructions on enabling pop-ups');
            alert('To enable pop-ups:\n' +
                '1. Open Chrome Settings\n' +
                '2. At the bottom of the page, click the "Show advanced settings..." link\n' +
                '3. Under the "Privacy" section, click the "Content Settings..." button\n' +
                '4. Scroll down to the "Pop-ups" section and select the "Allow all sites to show pop-ups" option\n' +
                '5. Click "Done" at the bottom of the modal window')
        }
    }
}