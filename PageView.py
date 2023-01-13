import io
import tkinter as tk
import cv2
import numpy as np
import pickle
import time
import math
import os

from PIL import ImageTk, Image
from google.cloud import vision
from google.api_core import retry

from TextEditModule import TextEditModule
from BoundedTextModule import BoundedTextModule


'''
THIS FILE CONTAINS A PAGE OBJECT
'''


class PageView:
    
    def __init__(self, root, file_name):
        self.text_modules = []
        self.file_name = file_name
        self.img = Image.open(file_name)
        self.file_reference = file_name.replace("/", "\\").split("\\")[-1]
        self.folder_path = "\\".join(file_name.replace("/", "\\").split("\\")[:-1]) 
        self.cache_path = self.folder_path + "\\cache\\"+ self.file_reference + ".p"        
        if not os.path.isdir(self.folder_path + "\\cache\\"):
            print("Created folder " + self.folder_path + "\\cache\\" )
            os.mkdir(self.folder_path + "\\cache\\")
        
        if not root:
            return
        
        self.canvas_height = root.canvas.winfo_height()
        self.img_ratio = 1
        if(self.canvas_height < self.img.height):
            self.img_ratio = self.canvas_height/self.img.height            
        self.img_tk = ImageTk.PhotoImage(self.resize_to_canvas(self.img))
        self.canvas_img = None
        self.master = root
        self.raw_ocr = {}
        self.ocr_data = {}
        self.indicator = None
        self.indicator_coords = []
        self.reselecting_bound = None
        self.loading_data = False
        
    def render(self):
        self.canvas_img = self.master.canvas.create_image(0, 0, image=self.img_tk, anchor=tk.NW)
        for module in self.text_modules:
            module.render()
        for module in self.text_modules:
            module.render_text()
        self.load_data()
    
    def load_data(self, display = True):
        if self.loading_data: return
        self.loading_data = True
        if not self.raw_ocr:
            self.load_ocr()
        if not self.text_modules:
            self.format_ocr(display)
        self.loading_data = False
            
    def load_ocr(self):
        if os.path.exists(self.cache_path):
            self.raw_ocr = pickle.load(open(self.cache_path, "rb"))
            print("Loaded OCR From Cache")
        else:
            self.raw_ocr = self.get_ocr(self.img)
            pickle.dump(self.raw_ocr, open(self.cache_path, "wb" ))

    def hide(self):
        for module in self.text_modules:
            module.hide()
            
    def delete(self):
        for module in self.text_modules:
            module.delete()
    
    def add_module(self, event):
        self.indicator_coords = [event.x, event.y, event.x, event.y]
        self.indicator = self.master.canvas.create_rectangle(self.indicator_coords, fill = '', outline = 'black')
        
    def move_module(self, event):
        self.indicator_coords[2] = event.x
        self.indicator_coords[3] = event.y        
        self.master.canvas.coords(self.indicator, *self.indicator_coords)     
        
    def release_module(self):
        coords = [int(x/self.img_ratio) for x in self.order_coords(self.indicator_coords)]
        if self.reselecting_bound:
            self.reselecting_bound.update_coords(coords)
            if self.reselecting_bound.fast_resizing:
                self.reselecting_bound.fast_resize = False
                self.reselecting_bound.text_render.get_img_bounds(True)
            self.reselecting_bound = None
        else:
            module = TextEditModule(self.master, self, coords)
            self.text_modules.append(module)
            module.render()
 
        self.master.canvas.delete(self.indicator)
        self.indicator = None
        self.indicator_coords = []
        
    def remove_module(self, module):
        self.text_modules.remove(module)
        
    def identify_click(self, event):
        for module in reversed(self.text_modules):
            if event.x > module.input.coords[0] and event.x < module.input.coords[2]:
                if event.y > module.input.coords[1] and event.y < module.input.coords[3]:
                    return module
        return False
    
    def get_ocr(self, image):
        try:
            print("Requesting OCR Data... ")
            img_byte_arr = io.BytesIO()
            format_string = self.file_name.split(".")[-1]
            if format_string.lower() == "jpg":
                format_string = "jpeg"
            image.save(img_byte_arr, format=format_string)
            img_byte_arr = img_byte_arr.getvalue() 
            img = vision.Image(content=img_byte_arr) 
            client = vision.ImageAnnotatorClient()
            start = time.time() * 1000
            print("Request Sent")
            response = client.document_text_detection(image=img, retry = retry.Retry(deadline=30))
            print("Request Recieved in " + str(math.floor(time.time() * 1000 - start)) + " milliseconds")
            texts = response.text_annotations 
            ocr_data = []
            for text in texts:
                v = text.bounding_poly.vertices
                ocr_data.append(BoundedTextModule(text.description, self.order_coords([v[0].x, v[0].y, v[2].x, v[2].y])))
            if ocr_data:
                print("Retrieved data: \n" + ocr_data[0].get_description())
                return ocr_data
            else:
                print("No text found")
                return "No Text Found"
        except Exception as e:
                print("Failed to get ocr: " + str(e))
                return []
            
        
    def format_ocr(self, display):
        if self.raw_ocr == "No Text Found": return
        
        print("Merging Groups...")
        groups = []
        
        if self.get_config("mode") == "text":
            group = BoundedTextModule()
            group.add_module(self.raw_ocr[0])
            groups.append(group)
        else:
            sentences = self.raw_ocr[0].get_description().split("\n")
            group = BoundedTextModule()
            current = 0
            for text in self.raw_ocr[1:]:
                group.add_module(text)
                if group.get_description().replace(" ", "") == sentences[current].replace(" ", ""):
                    module = BoundedTextModule()
                    module.add_module(group)
                    groups.append(module)
                    group = BoundedTextModule()
                    current += 1
            
        i,j=0,0
        while i < len(groups):
            if j == len(groups):
                i+=1
                j=0
            else:
                if i == j or not self.merge_if_close(groups, i, j, self.get_config("readingDirection")):
                    j+=1
        
        print("Rendering Modules...")
        for group in groups:
            try:
                if not self.is_good_string(group.get_description()):
                    print("Skipped text " + group.get_description())
                    continue
                module = TextEditModule(self.master, self, group.bound, group)
                self.text_modules.append(module)
                module.display_mode  = int(self.get_config("defaultRender"))
                module.text_render.get_img_bounds(True)
                if not display:
                    module.hide()
                print("")
            except Exception as e:
                print("Exception: " + str(e))
        if display:
            for module in self.text_modules:
                module.render_text()
            
        print("Done \n")
        
        
    def merge_if_close(self, arr, idx1, idx2, mode = "rtl"):
        close = False
        b1 = arr[idx1].bound
        b2 = arr[idx2].bound      
        ratio = 1.6
        #horizontal
        if b1[3] - b1[1] < b1[2] - b1[0] and b2[3] - b2[1] < b2[2] - b2[0]:
            if b1[0] < b2[2] and b2[0] < b1[2]:
                space = max([x.bound[3] - x.bound[1] for x in (arr[idx1].sub_modules + arr[idx2].sub_modules)])/ratio
                if abs(b2[1] - b1[3]) < space:
                    close = "top"
                elif abs(b1[1] - b2[3]) < space:
                    close = "bottom"  
        #vertical
        elif b1[3] - b1[1] >= b1[2] - b1[0] and b2[3] - b2[1] >= b2[2] - b2[0]:
            if b1[1] < b2[3] and b2[1] < b1[3]:
                space = max([x.bound[2] - x.bound[0] for x in (arr[idx1].sub_modules + arr[idx2].sub_modules)])/ratio
                if abs(b2[0] - b1[2]) < space:
                    close = "left"
                elif abs(b1[0] - b2[2]) < space:
                    close = "right"
        else:
            return False
        if not close: 
            return False

        if close == "top" or mode[0] == close[0]:
            arr[idx1].merge_module(arr[idx2])
        else:
            arr[idx1].merge_module(arr[idx2], 1)
        arr.remove(arr[idx2])
        return True
    
    def get_config(self, config_name):
        return self.master.config[config_name].get()
        
    
    def is_good_string(self, string):
        for c in string:
            if c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ\
                        0123456789!@#$%^&*()<>?,./{}[]:;|\"\'- ":
                return True
        return False
    
    def export_page(self, txt = False):
        (f_path, _, f_name_full) = self.file_name.replace("\\", "/").rpartition("/")
        (f_name, f_type) = f_name_full.split(".")
        if txt:
            f_type = "txt"
        output_file = self.get_config("convertPath").format(
            file_path = f_path, file_name = f_name, file_type = f_type)
        print("Saving to: " + output_file)
        if txt:
            with open(output_file, 'w', encoding="utf-8") as file:
                file.write('\n'.join([str(x) for x in self.text_modules]))
        else:
            ret = self.img.copy()
            for module in self.text_modules:
                try:
                    render = module.text_render
                    if render.bounding_img:
                        ret.paste(render.bounding_img, render.bounding_coords, render.bounding_img)
                except Exception as e:
                    print("Exception: " + str(e))
            for module in self.text_modules:
                try:
                    if module.text_render.img:
                        ret.paste(module.text_render.img, (module.coords[0], module.coords[1]))
                except Exception as e:
                    print("Exception: " + str(e))
            ret.save(output_file) 
        
    def order_coords(self, coords):
        return [min(coords[0], coords[2]), min(coords[1], coords[3]),
                max(coords[0], coords[2]), max(coords[1], coords[3])] 
        
    def resize_to_canvas(self, img):
        return img.resize((int(img.width*self.img_ratio+0.5), int(img.height*self.img_ratio+0.5)), Image.LANCZOS)
    
    
    
    
    
    