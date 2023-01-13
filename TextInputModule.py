import tkinter as tk

class TextInputModule:
    
    def __init__(self, coords, master, root):
        self.coords = coords
        self.master = master
        self.root = root
        self.canvas_bound, self.canvas_frame, self.config_input = None, None, None #lazyloaded
        self.INPUT_NAMES = ["imgText", "translatedText", "finalText"]
        self.data = {}
        self.inputs = {}
        self.CONFIG_OPTIONS = ["ocrLang", 
                               "inputLang", 
                               "outputLang", 
                               "textPadding", 
                               "textBorder", 
                               "borderType", 
                               "fontPath", 
                               "maxFontSize",
                               "bgScale",
                               "bgThreshold"]
        self.config = {}
        for key in self.CONFIG_OPTIONS:
            self.config[key] = tk.StringVar()
            self.config[key].set(root.config[key].get())
            
        #Helper Variables to remember state
        self.start_coords = [0,0]
        self.lockout = False
        self.view_config = False
        self.MIN_WIDTH = 250
        self.MIN_HEIGHT = 100
        self.MAX_WIDTH = 500
        self.MAX_HEIGHT = 300
        
    #if canvas_frame already exists, just moves it into position.
    #otherwise, creates a resizable canvas_frame with 3 inputs for img_text, translated_text, and final_text 
    def render(self):
        if not self.canvas_bound:
            self.canvas_bound = self.root.canvas.create_rectangle(*self.coords, fill='', outline = 'black')
        if self.canvas_frame:
            self.set_dimensions(self.coords[2], self.coords[1])
            return
        print("Creating UI for text: " + self.get_text("finalText"))
        
        self.canvas_frame = tk.Frame(self.root.canvas, bd=1)
        font_size = self.root.config["inputSize"].get()
        self.MIN_HEIGHT = (int(font_size) + 10) * 3 + 30
        for name in self.INPUT_NAMES:
            text_wrap = tk.Frame(self.canvas_frame)
            text_wrap.pack_propagate(0)
            text_wrap.pack(expand = True, fill = tk.BOTH)
            self.inputs[name] = tk.Text(text_wrap, font=("Courier", font_size))
            if name in self.data:
                self.set_text(name, self.data[name])
            self.inputs[name].pack()
        cf = tk.Frame(self.canvas_frame, height = 30)   
        cf.pack_propagate(0)
        button_config = [
            ["r1", self.master.update_ocr],
            ["r2", self.master.update_translation],
            ["cfg", self.toggle_config],
            ["uc", self.master.reselect_bound],
            ["ubg", self.master.text_render.get_img_bounds],
            ["frs", self.master.fast_resize],
            ["b2f", self.master.bring_to_front],
            ["del", self.master.delete],
            ["⅃", None],
            
        ]
        buttons = [tk.Button(cf, text=x[0], command=x[1]) for x in button_config]
        for button in buttons:
            button.pack(side = tk.LEFT, fill = tk.X, expand = True)
        cf.pack(fill = tk.X)
        buttons[-1].bind("<Button-1>", self.update_coords)
        buttons[-1].bind("<B1-Motion>", self.resize)
        
        self.set_dimensions(self.coords[2], self.coords[1], 
                           int(font_size) * len(self.get_text("finalText")), self.coords[3] - self.coords[1])    
    
    def set_dimensions(self, x, y, w = None, h = None):
        if w == None:
            w = self.canvas_frame.winfo_width()
        if h == None:
            h = self.canvas_frame.winfo_height()
        wc, hc = min(self.MAX_WIDTH, max(w, self.MIN_WIDTH)), min(self.MAX_HEIGHT, max(h, self.MIN_HEIGHT))
        xc = x if x < self.root.canvas.winfo_width() - wc else self.coords[0] - wc
        yc = min(y, self.root.canvas.winfo_height() - hc)
        self.canvas_frame.place(x = xc, y = yc, width = wc, height = hc)
    
    #create config_input. Want to create this lazily
    #as it has a lot of widgets and isn't necessary for most modules
    def make_config_input(self):
        self.config_input = tk.Frame(self.root.canvas)
        for i, key in enumerate(self.CONFIG_OPTIONS):
            tk.Label(self.config_input, text = key).grid(row = i, column = 0)
            tk.Entry(self.config_input, textvariable = self.config[key]).grid(row = i, column = 1)
    
    #Toggle config_input visible
    def toggle_config(self):
        if not self.config_input:
            self.make_config_input()
        if self.view_config:
            self.config_input.place(x=-1000,y=-1000)
            self.view_config = False
        else:
            if (self.coords[1] + self.canvas_frame.winfo_height() + self.config_input.winfo_height()
                > self.master.master.canvas_height):
                self.config_input.place(
                x=self.coords[2], y=self.coords[1] - self.config_input.winfo_height())
            else:
                self.config_input.place(
                    x=self.coords[2], y=self.coords[1] + self.canvas_frame.winfo_height())
            self.view_config = True
    
    #functions used for resizing of canvas_frame. surprisingly basic
    def update_coords(self, e):
        self.start_coords = [e.x, e.y]
        
    def resize(self, e):
        if self.lockout:
            self.lockout = False
            return
        self.set_dimensions(self.coords[2], self.coords[1], 
                           self.canvas_frame.winfo_width() - self.start_coords[0] + e.x,
                           self.canvas_frame.winfo_height() - self.start_coords[1] + e.y)
        self.lockout = True

    def get_text(self, text_type):
        if text_type in self.inputs:
            self.data[text_type] = self.inputs[text_type].get('1.0', tk.END).strip()
        if text_type in self.data:
            return self.data[text_type]
        return "None"
        
    def set_text(self, text_type, text):
        if text_type in self.inputs:
            self.inputs[text_type].delete('1.0', tk.END)
            self.inputs[text_type].insert(tk.END, text.strip())
        self.data[text_type] = text.strip()
        
    def get_config(self, key):
        return self.config[key].get()
    
    def hide(self):
        if self.canvas_bound:
            self.root.canvas.delete(self.canvas_bound)
            self.canvas_bound = None
        if self.canvas_frame:
            self.canvas_frame.place(x=-1000, y=-1000)
        if self.view_config:
            self.config_input.place(x=-1000,y=-1000)
            self.view_config = False
            
    def delete(self):
        if self.canvas_bound:
            self.root.canvas.delete(self.canvas_bound)
            self.canvas_bound = None
        if self.canvas_frame:
            self.canvas_frame.destroy()
        if self.config_input:
            self.config_input.destroy()
        