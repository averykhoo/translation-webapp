#   MT App

*   Web App
    *   Text Translation
    *   File Translation
    *   Other Features
*   APIs
    *   Translation
    *   Utils
    

#   Web App
*   PLEASE USE CHROME
    *   ideally v70+, there are known bugs if you use v52

##  Text Translation (Web App)
*   same idea as google translate, but more features
    *   same icon too because why not 
*   layout is responsive to window size / shape
    *   so you can resize the window and have it occupy less space
    *   or zoom in/out
*   text size is responsive to amount of text typed into the box
    *   starts at 2.5x default size, and dynamically shrinks as you type more
*   language detection built-in (server-based)
*   html and text is truncated server-side to about 6 MiB (doesn't account for unicode)
*   translations stored in browser history
    *   labelled in the page title (up to 50 chars)
    *   debounced along with translate
*   server error is flagged to user in the output box
*   if you enter more than 140 chars to translate, an alert shows to let you know translation is underway
    *   because longer input takes long enough to translate that we want to let the user know it's happening
*   glow around input box to make it obvious whether or not it's focused
*   shortcuts:
    *   ctrl + b / i / u for formatting
    *   esc to unfocus input box
    *   enter / space to focus input box
    *   usual copy paste stuff

### Supports rich text translation
*   formatting is retained in the translation
    *   this comes at the cost of translation quality, because the backend tries very hard not to break formatting
*   formatting buttons available
*   formatting removal also available (select text then click remove)
*   clearing the text box clears any remaining formatting 
*   inserting images/videos/links is not supported, as it doesn't produce translation output
    *   pasting images from Word tends to lead to the image being lost, but it doesn't really matter
    *   links are treated as text
*   tables are also supported, but they're hacked in
    *   cell selection/merging is broken in chrome v52
    *   cell formatting works too
        *   left click a cell to format it
    *   merged cells also work
        *   click and drag to select multiple cells, then right click and select merge
    *   resizing columns in the input table magically resizes the output table
        *   you can resize the output table separately too
        *   click the table then use the control bars that appear above the table
    *   there's a patch hacked in to fix chrome reading garbage outside the clipboard html buffer if pasting from word



##  File Translation (Web App)
1.  choose input language (no langID, as we can't detect language for OCR)
2.  upload files
    *   up to 5 files total
        *   max size of each file is 5 MB
        *   server-side checks drop anything above 6 MiB
        *   limits imposed because files go into the same queue as text translation
    *   limits on filetype based on what the backend can handle (allows pdfs, images, office)
        *   except old office files ppt and xls (pptx and xlsx okay)
    *   once you upload any file, you cannot change the input language until you refresh / remove all files
    *   icons shown are chosen based on the filetype
    *   files are MD5-hashed upon upload in the browser for validation
        *   but I didn't bother to implement checking in the backend
        *   it'll be obvious to the user if the file is corrupted
        *   it's trivial for the user to just re-upload that file
3.  translate server-side
    *   files are deduped via sha256 and extension
    *   if file is already translated / translation is already in progress, don't touch it
        *   if two people upload the same file and one person cancels it, the other person's translation also cancels
        *   but this is very unlikely to happen so meh whatever
    *   while file is translating, user sees an animated spinner
        *   also reports which translation process step the backend is at
4.  download translated files
    *   download will become available once the backend has finished translating


##  Other Stuff
*   built-in hello world in the menu because why not
*   easter egg / april fool's day
    *   double-click the navbar (at the top)
*   over-engineered bookmarklet
    *   select text, then click the bookmarklet to translate the selected text 
        *   plaintext copying only (reading formatted text as html from a webpage is harder than it seems)
    *   error alert if server is offline
    *   remote script loading so that we can update their bookmarklet logic
    *   if you're in an mt app and navigating to another mt app (e.g. xl -> duo), retains formatted text content
    *   if you block pop-ups, it gives you the option to use the current tab, or tells you how to solve it
    *   info text in the navbar
*   dual-output translation
    *   you'll need a second MT system for this to make sense
    *   for now it just has one formatted output and one plaintext output
*   large-format translation
    *   for people who want bigger boxes
    *   only the box size is different



#   APIs (implemented in `blueprint_translation.py`)

##  text/html translation:
*   POST
    *   input_lang
    *   output_lang
    *   input_text / input_html
*   returns
    *   translated text or html
    
##  file translation via POST then polling
*   upload
    *   POST to `/translation/upload`
        *   uuid
        *   input_lang
        *   output_lang
        *   lots of other stuff you don't really need but should be useful
        *   single file (via `FILES['file']`)
    *   returns
        *   True (if translation started or already running or complete) or False
*   status polling
    *   POST to `/translation/status`
        *   uuid
    *   returns json
        *   download url (or None)
        *   download filename (or None)
        *   download label (or None)
        *   status
*   download
    *   GET from `/translation/download/<uuid>`
*   cancel
    *   POST to `/translation/upload`
        *   uuid
        *   removed = True
    *   returns
        *   False (probably)


#  TODO
*   dictionary lookups instead of translating single words
*   acronym definitions shown in input box using cursors module
    *   maybe show info cards for each acronym
*   swap language button
*   track usage 
    *   track usage accurately (despite constant re-translation)
    *   telemetry
*   detect language and suggest alternative if user selected wrong language
    *   low priority because user will know if it's not translating


##  Cursors
*   `input_quill.getModule('cursors').createCursor('cursor', 'user 1', 'red')`
*   `input_quill.getModule('cursors').moveCursor('cursor', {index:2, length:2})`
*   todo: clear cursors when input clears
