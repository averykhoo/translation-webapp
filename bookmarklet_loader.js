if (window.BOOKMARKLET_RUNNING) {
    console.log('please wait for previous bookmarklet instance to finish running');
    console.log('Bookmarklet has not finished running, please wait...');

} else {
    console.log('starting bookmarklet loader', new Date());
    window.BOOKMARKLET_RUNNING = true;

    console.log('loading and injecting bookmarklet script');
    const script = document.createElement("script");
    script.type = "text/javascript";
    script.src = "{MT_URL}/bookmarklet_script";
    document.body.appendChild(script);

    script.onload = function () {
        console.log('script loaded, running bookmarklet');
        bookmarklet_run("{TARGET_URL}");
        console.log('bookmarklet finished, unloading script');
        document.body.removeChild(this);
        console.log('script unloaded');
        window.BOOKMARKLET_RUNNING = false;
        console.log('succeeded', new Date());
    };

    script.onerror = function (event) {
        console.log('script failed to load');
        console.log(event);
        alert("ERROR: bookmarklet could not reach the MT server, has the URL changed? \n(URL: {MT_URL})");
        window.BOOKMARKLET_RUNNING = false;
        console.log('failed', new Date());
    };
}