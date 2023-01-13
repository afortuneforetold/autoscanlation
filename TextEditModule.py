from BoundedTextModule import BoundedTextModule
from TextInputModule import TextInputModule
from TranslatedTextModule import TranslatedTextModule


'''
THIS IS THE OVERALL CLASS THAT CONTAINS A 
BOUNDEDTEXTMODULE (FOR TEXT LOCATION)
TEXTINPUTMODULE (FOR USER INPUT) AND
TRANSLATEDTEXTMODULE (FOR RENDERERING TRANSLATED TEXT)
'''

class TextEditModule:   
    
    def __init__(self, root, master, coords, data = {}):
        self.coords = coords                #coords on image
        self.img = master.img.crop(coords)  #PIL Subimage of original image 
        self.img_data = data                 #raw data from OCR              
        self.root = root                    #root
        self.master = master                #page the module is on

        self.input = TextInputModule(       #Data input
            [int(x*master.img_ratio) for x in coords], self, root)
        self.text_render = TranslatedTextModule(self, master, root)   #typset image form of text
        
        self.show_border = False             #Whether to show a black border on typset text
        self.display_mode = 0                #0 = text editing, 1 = typeset version
        self.fast_resizing = False
        
        if data:
            self.load_text() 
            

    def update_ocr(self):
        data = self.master.get_ocr(self.img)
        self.img_data = BoundedTextModule()
        for module in data[1:]:
            self.img_data.add_module(module)
        self.load_text()
    
    def load_text(self):
        self.input.set_text("imgText", self.img_data.get_description().replace("\n", ""))
        self.update_translation()
        
    def get_google_translate(self):
        return  self.root.google_translate_client.translate(self.input.get_text("imgText"), 
                            target_language=self.input.get_config("outputLang"), format_='text')["translatedText"]
    
    def get_deepl_translate(self):
        t_lang = self.input.get_config("outputLang")
        if t_lang == "en":
            t_lang += "-us"
        return self.root.deepl_translator.translate_text(self.input.get_text("imgText"), 
                            target_lang=t_lang).text
    
    def update_translation(self):
        if self.root.config["translator"].get() == "deepl":
            print("Getting DeepL Translation")
            translated_text = self.get_deepl_translate()
        else:
            print("Getting Google Translation")
            translated_text = self.get_google_translate()
        self.input.set_text("translatedText", translated_text)
        self.input.set_text("finalText", translated_text)
        print("Got translation: " + translated_text)
            
    def update_display_mode(self):
        self.display_mode = (self.display_mode + 1) % 2
        self.render()
        
    #hides all elements then renders appropriate ones.
    def render(self, display_mode = -1):
        if display_mode >= 0:
            self.display_mode = display_mode
            
        self.hide()            
        if self.display_mode == 0:
            self.input.render()            
        else:
            self.text_render.render() 
            
    def render_text(self):
        if self.display_mode == 1:
            self.text_render.render_text() 
            
    def fast_resize(self):
        self.fast_resizing = True
        print("test")
        self.reselect_bound()
            
    def update_coords(self, coords):
        self.coords = coords
        self.img = self.master.img.crop(coords)
        self.input.coords = [int(x*self.master.img_ratio) for x in coords]
        self.text_render.text = ''
        self.render()
        
    def reselect_bound(self):
        self.hide()
        self.master.reselecting_bound = self
        
    def bring_to_front(self):
        lst = self.master.text_modules
        lst.append(lst.pop(lst.index(self)))
        self.render()
        
    def hide(self):
        self.input.hide()
        self.text_render.hide()
        
    def delete(self):
        self.input.delete()
        self.text_render.delete()
        self.master.remove_module(self)
        
    def __str__(self):
        return '\t'.join([self.input.get_text(x) for x in self.input.INPUT_NAMES] + [str(self.coords)])



    
