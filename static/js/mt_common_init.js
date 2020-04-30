// language codes
const language_codes_mapping = {
    'en': 'English',
    'ms': 'Malay',
    'zh': 'Chinese (Simplified)',
    'id': 'Indonesian',
    'ar': 'Arabic',
    'vi': 'Vietnamese',
    'th': 'Thai',
};

function get_chrome_version(){
    // read user agent
    let chrome_str = window.navigator.userAgent.match(/Chrome\/\d+/)[0];

    // not chrome
    if (!chrome_str){
        return -1
    }

    return parseInt(chrome_str.substr(7))
}

// configure sparkles here since it's not really part of the mt logic
document.addEventListener("DOMContentLoaded", function () {
    const $nav_bar = $('#nav_bar');
    const $bookmarklet = $('#bookmarklet');
    const $menu_button = $('#menu_button');
    const $sparkle_text = $('#sparkle_text');

    // what's today's date
    const today = new Date();
    const is_april_fools = today.getMonth() === 3 && today.getDate() === 1;

    // disable mouse sparkles by default EXCEPT on April Fool's day
    if (is_april_fools) {
        sparkle(true);
        $sparkle_text.show();
    } else {
        sparkle(false);
        $sparkle_text.hide();
    }

    // toggle mouse sparkles when you double-click the navbar (also unselect any accidentally selected text)
    $nav_bar.on('dblclick', function () {
        sparkle(); // toggle
        $sparkle_text.toggle();

        // unselect things that were accidentally selected
        if (window.getSelection) {
            if (window.getSelection().empty) {
                window.getSelection().empty();
            } else if (window.getSelection().removeAllRanges) {
                window.getSelection().removeAllRanges();
            }
        }
    });

    // un-toggle mouse sparkles if you're double-clicking the bookmarklet button, which happens to be on the navbar
    $bookmarklet.on('dblclick', function () {
        sparkle(); // toggle
        $sparkle_text.toggle();
    });

    // un-toggle mouse sparkles if you're double-clicking the menu button, which also appens to be on the navbar
    $menu_button.on('dblclick', function () {
        sparkle(); // toggle
        $sparkle_text.toggle();
    });
});
