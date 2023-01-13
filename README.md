# Manga MTL Tool

## Initial setup:
To use this program, you must either clone the repo and install the required libraries or download and extract the zip file ([link here](https://gitlab.com/afortuneforetold/manga-mtl/-/raw/master/MangaMTL.zip)). Next, you must go and create a google developer account, create a project, and add the cloud vision API and google translate API referencing the steps [here](https://cloud.google.com/vision/docs/quickstart-client-libraries) and [here](https://cloud.google.com/translate/docs/setup). Finally, you must create a folder called /auth in the project/executable folder and place the json file with your credentials inside. 

## Feature Description
### Navbar:
* The top left of the navbar contains the file dropdown. Select a file from it to load the image. Note that the image is automatically resized, but the OCR/export is always done on the high quality original
* Next, we have +, <, and >, which allows you to add and navigate files.
* Config opens the option menu, which will be discussed further below. You can click save to preserve settings between sessions
* Export Page/Export all: Export all rendered text modules to the path in `config.convertPath`
* Export Txt/Export all txt: Export data to same path but as a txt file containing text and boundaries
* Delete/Delete all: must be used every once in a while (I recommend every chapter) or the application will crash from having too many pages loaded in the background
* Build Cache. Select a folder with images to automatically build a cache of OCR responses. Will considerably speed up the program if done before running it.

### Modules:
* Left clicking and dragging creates a text module on the canvas. Modules are also automatically created when the page is first loaded.
* Each module has 3 input boxes: The first contains the raw text, the second contains translated text, and the third contains text that will be rendered by the typesetting feature (you should manually edit this text)
* Right clicking on a module toggles between input mode and typesetting mode, where the text is automatically placed within the bounds of the module. You MUST have the module in typesetting mode if you want it to be rendered accurately upon export
* The buttons at the bottom all have very important functionalities
 * `r1` reloads the OCR API within the bounds of the box, and updates translation as well
 * `r2` updates translations if you've made manual changes to the raw text, which is sometimes required  
 * `cfg` opens the manual-specific option menu, which is discussed below.
 * `uc` updates the coordinates of the module by allowing you to draw a new boundary for the module with left click drag
 * `ubg` updates the background mask, which is a while area that fills the entire speech bubble and is useful if the boundaries of the English text don't cover the entire raw text (the English text will always have a while background)
 *  `b2f` brings the image to front, which doesn't do much in the preview but will place it in front in the rendered image
 * `frs` is a fast resize that automatically snaps to detected boundaries and fills in the background.
 * `del` deletes the module
 * the bottom right button allows you to resize the input box

### Config
* `ocrLang` is the language of the raw text. Currently doesn't do anything because Google is really good at detecting language
* `inputLang`, `outputLang` are the input and output languages for the translation api. Valid keys are shown in the `Available langs` dropdown on the bottom of the menu
* `convertPath` is the path of the exported file. This can be directed to a subfolder (like `{filePath}/converted/{fileName}.{fileType}`, although if you wish to do so you must manually create the folder first
* `fontPath` is the path of the font to be used when rendering the automatic typsetting. BE SURE TO SET THIS UP OR IT WON'T WORK
* `inputSize` is the font size of the text input modules. I have no idea why I implemented this
* `textPadding` is the padding of the text within the bounding box. It should be four integers separated by spaces, which form the left, top, right, and bottom padding respectively
* `textBorder` is the width of the border box. Note that if this is not 0, the speech-bubble fill mask will instead be replaced with a visible border to make the text appear as if it's in a description box. This is useful when overwriting text that is not bounded by a speech bubble and is just layered over the image, as you can avoid redrawing it and just pretend it was in a box all along.
* `defaultRender` is the format with which text boxes are rendered when the page is first loaded (manually created text boxes always render in input mode as the initialize with no text). 0 is input mode, 1 is typesetting mode
* `maxFontSize` determines the max font size in an image. While the image is automatically resized to fit your screen, this is the true font size so it may be too big or small depending on the image resolution
* `threshold` determines the cutoff for the background autofill. If large amounts of your image are being filled with white, lower the threshold
* **IMPORTANT:** `ocrLang`, `inputLang`, `outputLang`, `textPadding`, and `textBorder` are unique to each module, and to actually change them you have to change them in the module's config menu. Changing them in the main navbar simply changes the default value for any *new* modules created

## FAQ
* What languages are supported? 
    * Any language Google supports. Just be sure to update the language in config
* I clicked [+] added some files and nothing is happening
    * Select the file from the dropdown
* The image in the window looks really weird
    * This is the result of automatic resizing and/or layering issues and should be fixed in the exported version. You can export the page to check on how it actually looks, as the displayed image in the window is basically just an approximation
* Something doesn't work, why?
    * Check the console for an exception. Common errors include not having the right packages installed, not properly configuring Google Cloud Vision credentials, having an invalid typesetting font path/export path, or having improperly formatted config options. If it is none of the above, feel free to submit a bug report.
* X feature doesn't work the way I expect it to
    * This was a side project of mine, and I cut a few corners in the process. Again, feel free to request new features/suggest corrections for existing ones.



