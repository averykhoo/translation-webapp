document.addEventListener("DOMContentLoaded", function () {
    const $top_10_spacer = $("#top_10_spacer");
    const $top_15_spacer = $("#top_15_spacer");
    const $input_lang_option = $("input[name=input_language]");
    const $input_language_header = $("#input_language_header");
    const $upload_card = $("#upload_card");
    const $upload_header = $("#upload_header");
    const $download_card = $("#download_card");

    $input_lang_option.on('change', function () {
        $top_15_spacer.collapse('hide');
        $input_language_header.collapse('hide');
        $upload_card.collapse('show');
    });

    // file upload dropzone
    const $dropzone = $('#dropzone_box').dropzone({
        url: "/translation/upload",
        addRemoveLinks: true,  // allow file removal
        timeout: 60000, // allow 1 min for slow file uploads on the slow network
        maxFiles: 5,
        maxFilesize: 5,  // 5 MB
        parallelUploads: 1,  // rate-limit, hopefully reducing backend processing load
        acceptedFiles:
            '.pdf,' +
            '.bmp, .jpg, .jpeg, .png, .tif, .tiff,' +
            '.doc, .docx, .pptx, .xlsx,' +
            '.odt, .odp, .ods,' +
            '.rtf, .txt, .htm, .html, .xhtml',
        accept: function (file, done) {
            if (file.name.toLowerCase().startsWith('~$')) {
                done('temp files not allowed');
            } else {
                done();
            }
        },
        init: function () {

            // when each file is added to the box, let the server know some details
            this.on('addedfile', function (file) {
                $input_lang_option.prop('disabled', true);
                $upload_header.collapse('hide');

                // push info to the server
                $.ajax({
                    data: {
                        uuid: file.upload.uuid,
                        added: true,
                        filename: file.name,
                        last_modified: file.lastModified,
                        last_modified_date: file.lastModifiedDate, // duplicate?
                        size: file.size,
                        type: file.type,
                        input_lang: $("input[name=input_language]:checked").val(),
                        output_lang: 'en',
                    },
                    type: 'POST',
                    url: '/translation/upload',
                });

                // update preview icon
                let preview_icon_url = '/translation/icon/' + file.name;
                $(file.previewElement).find(".dz-image img").attr('src', preview_icon_url);

                // start hashing the file
                async_update_md5(file);
            });

            // make sure to let the server know the uuid of each uploaded file
            this.on('sending', function (file, xhr, formData) {
                formData.append('uuid', file.upload.uuid);
                formData.append('size', file.size);
                formData.append('filename', file.name);
            });

            // when file is fully uploaded, add to set of active files
            this.on('success', function (file) {
                $top_10_spacer.collapse('hide');
                $download_card.collapse('show');

                start_polling(file.upload.uuid);
                uploaded_uuid.add(file.upload.uuid);
                const now = new Date();
                download_listjs.add([{
                    download_uuid: file.upload.uuid,
                    download_datetime: now.toISOString(),
                    download_name: file.name,
                    download_lang: language_codes_mapping[$("input[name=input_language]:checked").val()] +
                        " &rarr; English",
                    download_text: 'Processing...',
                    download_link: '<div class="spinner-border text-primary" role="status"><span class="sr-only">Loading...</span></div>',
                }]);
            });

            // remove files that fail to upload (use jquery to make it fade out instead of blink out)
            this.on('error', function (file) {
                setTimeout(function () {
                    const that = this;
                    $(file.previewElement).fadeOut({
                        complete: function () {
                            that.removeFile(file);
                        }
                    });
                }.bind(this), 2500);
            });

            // when file is removed, also notify the server
            this.on('removedfile', function (file) {
                uploaded_uuid.delete(file.upload.uuid);
                download_listjs.remove('download_uuid', file.upload.uuid);
                stop_polling(file.upload.uuid);
                $.ajax({
                    data: {
                        uuid: file.upload.uuid,
                        removed: true,
                    },
                    type: 'POST',
                    url: '/translation/upload',
                });
                if (uploaded_uuid.size === 0) {
                    $input_lang_option.prop('disabled', false);
                    $upload_header.collapse('show');
                    $top_10_spacer.collapse('show');
                    $download_card.collapse('hide');
                }
            });
        },
    });


    // initialize downloads list
    const download_listjs = new List('download_list', listjs_options);

    // actively poll the server for status of file to download
    function start_polling(uuid, timeout_seconds = 725) {  // magic number makes the spinner animation smooth
        processing_polling_timers.set(uuid, setTimeout(function () {
            $.ajax({
                data: {
                    uuid: uuid,
                },
                type: 'POST',
                url: '/translation/status',
                dataType: 'json',
                success: function (data) {
                    console.log(data);
                    const item = download_listjs.get('download_uuid', uuid)[0]._values;
                    item['download_text'] = data['status_text'];
                    download_listjs.remove('download_uuid', uuid);

                    if (data['link_url']) {
                        item['download_link'] = '<a class="btn btn-primary" href = "' + data['link_url'] +
                            '" download="' + data['link_name'] + '">' + data['link_text'] + '</a>';
                        stop_polling(uuid);
                    } else {
                        clearTimeout(processing_polling_timers.get(uuid));
                        start_polling(uuid);
                    }

                    download_listjs.add(item);
                    download_listjs.sort('download_datetime', {order: 'asc'});  // newest at the bottom
                }
            });
        }, timeout_seconds));
    }

    // stop polling for status
    function stop_polling(uuid) {
        clearTimeout(processing_polling_timers.get(uuid));
        processing_polling_timers.delete(uuid);
    }

});