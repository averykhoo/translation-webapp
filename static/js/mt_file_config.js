Dropzone.autoDiscover = false;
const processing_polling_timers = new Map();
const uploaded_uuid = new Set();
const uuid_md5 = new Map();

const listjs_options = {
    valueNames: ['download_uuid', 'download_name', 'download_lang', 'download_text', 'download_link'],
    item: '<li class="list-group-item">' +
        '      <p class="d-none download_datetime"></p>' +
        '      <p class="d-none download_uuid"></p>' +
        '      <h5 class="card-title download_name"></h5>' +
        '      <h6 class="card-subtitle download_lang"></h6>' +
        '      <p class="card-body download_text"></p>' +
        '      <p class="download_link"></p>' +
        '  </li>',
};


// calculate MD5 of the file and update the
function async_update_md5(file) {

    const chunk_size = 2 * 1024 * 1024; // read in chunks of 2MB
    const chunks = Math.ceil(file.size / chunk_size);
    const spark = new SparkMD5();
    const file_reader = new FileReader();
    const start_time = new Date().getTime();
    let currentChunk = 0;

    file_reader.onload = function (e) {
        console.log('Read chunk number ' + (currentChunk + 1) + ' of ' + chunks);

        spark.appendBinary(e.target.result); // append array buffer
        currentChunk += 1;

        if (currentChunk < chunks) {
            loadNext();
        } else {
            const md5_hash = spark.end();
            console.log('Finished loading! ');
            console.log('Computed hash: ' + md5_hash); // compute hash
            console.log('Total time ' + (new Date().getTime() - start_time));
            uuid_md5.set(file.upload.uuid, md5_hash);
            $.ajax({
                data: {
                    uuid: file.upload.uuid,
                    md5_hash: md5_hash,
                    md5_elapsed: (new Date().getTime() - start_time),
                },
                type: 'POST',
                url: '/translation/upload',
            });
            console.log(uuid_md5)
        }
    };

    file_reader.onerror = function () {
        console.log('Oops, something went wrong.');
    };

    function loadNext() {
        const start = currentChunk * chunk_size;
        const end = start + chunk_size >= file.size ? file.size : start + chunk_size;

        file_reader.readAsBinaryString(File.prototype.slice.call(file, start, end));
    }

    console.log('Starting incremental hash (' + file.name + ')');
    loadNext();
}