import tkinter.filedialog
import tkinter as tk
import threading
import os

from google.cloud import vision
from google.cloud import translate_v2 as translate
import deepl 

from functools import partial, update_wrapper
from PageView import PageView


'''
THIS FILE INITIATES AUTHENTICATION ENVIRONMENT AND MAIN WINDOW
'''

def init():
    auth_folder = os.path.dirname(os.path.abspath(__file__))+"\\auth"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] =  auth_folder + "\\" + os.listdir(auth_folder)[0]
    main()

#create application window
def main():

    #init root constants/defaults
    root = tk.Tk()
    root.NAVBAR_HEIGHT=40
    root.ocr_client = vision.ImageAnnotatorClient()
    root.google_translate_client = translate.Client()
    root.deepl_translator = None
    root.TRANSLANGS = [u"{name} ({language})".format(**language)
                       for language in root.google_translate_client.get_languages()]  
    root.state('zoomed')
    root.settings_path = os.path.dirname(os.path.abspath(__file__)) + "\\settings.txt"
    
    #init Root Config
    root.config = {}
    load_config(root)
    
    #Root Page List. Key is file path, value is file object
    root.pages = {}    
    
    #init navbar
    root.navbar = tk.Frame(master = root, height = root.NAVBAR_HEIGHT)
    root.navbar.pack_propagate(False)
    root.navbar.pack(fill=tk.X)

    #init navbar file dropdown
    root.file_label = tk.Label(root.navbar, text="Files:")
    root.file_label.pack(side=tk.LEFT)
    root.previous_file = ""               #The currently selected file. Hidden when new file loaded
    root.active_file = tk.StringVar(root) #The path of the current file
    root.active_file.set("")
    root.active_file.trace_add("write", partial(render_page, root))
    root.file_list = [""]
    root.file_dropdown = tk.OptionMenu(root.navbar, root.active_file, "")
    root.file_dropdown.config(width=75)
    root.file_dropdown.pack(side=tk.LEFT)
    
    #init navbar file add and navigation buttons
    root.add_file_button = tk.Button(root.navbar, text="+", command=partial(add_files, root))
    root.add_file_button.pack(side=tk.LEFT)
    root.left_button = tk.Button(root.navbar, text="<", command=partial(prev_file, root))
    root.left_button.pack(side=tk.LEFT)
    root.right_button = tk.Button(root.navbar, text=">", command=partial(next_file, root))
    root.right_button.pack(side=tk.LEFT)
    
    #init config editor
    root.config_button = tk.Button(root.navbar, text="Config", command=partial(toggle_config, root))
    root.config_button.pack(side=tk.LEFT)
    root.config_input = tk.Frame(root)
    for i, key in enumerate(root.config): 
        tk.Label(root.config_input, text = key).grid(row = i, column = 0)
        tk.Entry(root.config_input, textvariable = root.config[key], width = 50).grid(row = i, column = 1)
    tk.Label(root.config_input, text = "Available langs:").grid(row = i+1, column = 0)
    tk.OptionMenu(root.config_input, None, *root.TRANSLANGS).grid(row = i+1, column = 1)  
    root.save_button = tk.Button(root.config_input, text = "Save", command = partial(save_config, root))
    root.save_button.grid(row = i + 2, column = 0)
    
    #init proper noun editor
    #TODO
    root.replace_button = tk.Button(root.navbar, text="Names", command=partial(update_replace, root))
    root.replace_button.pack(side=tk.LEFT)
    
    #init exporter
    root.export_button = tk.Button(root.navbar, text="Export Page", command=partial(export_page, root))
    root.export_button.pack(side=tk.LEFT)
    root.export_all_button = tk.Button(root.navbar, text="Export All", command=partial(export_all, root))
    root.export_all_button.pack(side=tk.LEFT)
    root.export_button = tk.Button(root.navbar, text="Export Txt", command=partial(export_page, root, True))
    root.export_button.pack(side=tk.LEFT)
    root.export_all_button = tk.Button(root.navbar, text="Export All Txt", command=partial(export_all, root, True))
    root.export_all_button.pack(side=tk.LEFT)
    root.delete_button = tk.Button(root.navbar, text="Delete", command=partial(delete_page, root))
    root.delete_button.pack(side=tk.LEFT)
    root.delete_all_button = tk.Button(root.navbar, text="Delete All", command=partial(delete_all, root))
    root.delete_all_button.pack(side=tk.LEFT)
    
    #Cache builder
    root.make_cache_button = tk.Button(root.navbar, text="Build Cache", command=partial(make_cache, root))
    root.make_cache_button.pack(side=tk.LEFT)
    
    #init canvas
    root.canvas_frame = tk.Frame(root, width = 300, height = 300)
    root.canvas_frame.pack(fill=tk.BOTH, expand=True)
    root.canvas = tk.Canvas(root.canvas_frame, bg="white", width = 1080, height = 1920)   
    root.canvas.bind("<Button-1>", partial(create_module, root))
    root.canvas.bind("<B1-Motion>", partial(move_module, root))
    root.canvas.bind("<ButtonRelease-1>", partial(release_module, root))
    root.canvas.bind("<Button-3>", partial(change_module_display, root))
    root.canvas.pack(fill=tk.BOTH, expand=tk.YES)   
    
    root.mainloop()

#Update List of files in back end
def add_files(root):
    for file in tk.filedialog.askopenfilenames():
        if not file in root.file_list:
            root.file_list.append(file)
    update_file_dropdown(root)
    
#Update dropdown to match file list
def update_file_dropdown(root):
    menu = root.file_dropdown["menu"]
    menu.delete(0, "end")
    for file in root.file_list:
        menu.add_command(label=file, command = lambda value=file: root.active_file.set(value))
        
#Toggle Config Menu Visible
def toggle_config(root):
    root.config_input.lift()
    if(root.config_input.winfo_x() > 0):
        root.config_input.place(x=-1000, y= -1000)
    else:
        root.config_input.place(x=400, y=root.NAVBAR_HEIGHT)

#Toggle Replace Menu Visible
def update_replace(root):
    pass

#Load Previous Page
def prev_file(root):
    index = root.file_list.index(root.active_file.get()) 
    if index > 1:
        root.active_file.set(root.file_list[index - 1])
        
#Load Next Page
def next_file(root):
    index = root.file_list.index(root.active_file.get()) 
    if index < len(root.file_list) - 1:
        root.active_file.set(root.file_list[index + 1])
        
def preload(root):
    index = root.file_list.index(root.active_file.get()) 
    for i in range(index + 1, index + 1 + int(root.config["preload"].get())):
        if i < len(root.file_list):
            file_name = root.file_list[i]
            if file_name == "": return
            if not file_name in root.pages:
                print("Preloading file " + file_name)
                root.pages[file_name] = PageView(root, file_name)
                t = threading.Thread(target=root.pages[file_name].load_data, args=(False,), daemon=True)
                t.start()
                
#Load Page by adding to root.pages, clearing canvas, 
#hiding previous page, and calling page.render()
def render_page(root, *args):
    file_name = root.active_file.get()
    if file_name == "": return
    if not file_name in root.pages:
        root.pages[file_name] = PageView(root, file_name)
    page = root.pages[file_name]
    root.canvas.delete(tk.ALL) 
    if not root.previous_file == "":
        root.pages[root.previous_file].hide()
    root.previous_file = file_name
    page.render()   
    preload(root)
    
def delete_page(root):
    file_name = root.active_file.get()
    if file_name == "": return
    if file_name in root.pages:
        root.pages[file_name].delete()
        del root.pages[file_name]
    root.canvas.delete(tk.ALL) 
    root.active_file.set("")
    root.previous_file = ""
    root.file_list.remove(file_name)
    update_file_dropdown(root)

def delete_all(root):
    for file_name in root.pages:
        root.pages[file_name].delete()
    root.canvas.delete(tk.ALL) 
    root.pages = {}
    root.active_file.set("")
    root.file_list = [""]
    root.previous_file = ""
    update_file_dropdown(root)
    
    
def export_page(root, txt = False):
    if root.active_file.get() in root.pages:
        root.pages[root.active_file.get()].export_page(txt)

def export_all(root, txt = False):
    for page in root.pages:
        root.pages[page].export_page(txt)
    
def create_module(root, event):
    if root.active_file.get() in root.pages:
        root.pages[root.active_file.get()].add_module(event)
    
def move_module(root, event):
    if root.active_file.get() in root.pages:
        root.pages[root.active_file.get()].move_module(event)
    
def release_module(root, event):
    if root.active_file.get() in root.pages:
        root.pages[root.active_file.get()].release_module()
        
def change_module_display(root, event):
    if root.active_file.get() in root.pages:
        module = root.pages[root.active_file.get()].identify_click(event)
        if module:
            module.update_display_mode()
            
def load_config(root):
    config_data  = {
        "ocrLang" : "",
        "inputLang": "ja",
        "outputLang" : "en",
        "translator" : "google",
        "deeplApiKey": "",
        "convertPath" : r"{filePath}/converted_{fileName}.{fileType}",
        "fontPath" : os.path.dirname(os.path.abspath(__file__)) + r"/fonts/wildwordsroman.ttf",
        "inputSize" : "10",
        "textPadding": "0 0 0 0",
        "textBorder" : "0",
        "borderType" : "solid",
        "defaultRender": "1",
        "maxFontSize" : "30",
        "bgScale" : "2",
        "bgThreshold" : "10",
        "readingDirection" : "rtl",
        "mode" : "manga",
        "preload": "0"
    }
    with open(root.settings_path, "a+") as file:
        file.seek(0)
        for setting in file.readlines():
            k, v = setting.split("=", 1)
            if k in config_data:
                config_data[k] = v.strip()
        
    for key in config_data:
        root.config[key] = tk.StringVar()
        root.config[key].set(config_data[key])
    set_deepl(root)

def save_config(root):
    with open(root.settings_path, "w+") as file:
        for k,v in root.config.items():
            file.write(k + "=" + v.get() + "\n")
    set_deepl(root)
            
def set_deepl(root):
    try: 
        root.deepl_translator = deepl.Translator(root.config["deeplApiKey"].get()) 
    except Exception:
        print("Invalid Deepl API Key")
            
def make_cache(root):
    ocr_folder(tk.filedialog.askdirectory())
            
def request_ocr(file_path):
    print("Starting file OCR: " + file_path)
    PageView(None, file_path).load_ocr()
    print("Saved file data")

def ocr_folder(folder_name):
    if not os.path.isdir(folder_name + "\\cache\\"):
        print("Created folder " + folder_name + "\\cache\\" )
        os.mkdir(folder_name + "\\cache\\")
    try:
        for file_name in os.listdir(folder_name):
            try:
                file_path = folder_name + "/" + file_name
                t = threading.Thread(target=request_ocr, args=(file_path,), daemon=True)
                t.start()
            except Exception as e:
                print("Exception : " + str(e) + "\n")
    except Exception as e:
        print("Exception " + str(e))
        



init()