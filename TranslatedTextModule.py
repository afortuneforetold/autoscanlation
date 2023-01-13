import tkinter as tk
from PIL import ImageTk, Image, ImageDraw, ImageFont
import cv2
import numpy as np

class TranslatedTextModule:
    
    def __init__(self, master, page, root):
        self.text = ''
        self.padding = "0 0 0 0"
        self.border = 0
        self.master = master
        self.page = page
        self.root = root
        self.img, self.tk_img, self.canvas_img = None, None, None
        self.bounding_coords = []
        self.bounding_img, self.bounding_img_tk, self.canvas_bound = None, None, None
        
    def make_gradient(self):
        c = self.master.coords
        self.bounding_img = Image.new('RGBA', [c[2]-c[0]+2*self.border, c[3]-c[1]+2*self.border], (0,0,0))
        self.bounding_img_tk = ImageTk.PhotoImage(self.page.resize_to_canvas(self.bounding_img))
        self.bounding_coords = [c[0] - self.border, c[1] - self.border]
    
    def make_border(self):
        c = self.master.coords
        self.bounding_img = Image.new('RGBA', [c[2]-c[0]+2*self.border, c[3]-c[1]+2*self.border], (0,0,0))
        self.bounding_img_tk = ImageTk.PhotoImage(self.page.resize_to_canvas(self.bounding_img))
        self.bounding_coords = [c[0] - self.border, c[1] - self.border]
        
    def get_img_bounds(self, update_coords = False):
        if not self.master.input.config["textBorder"].get() == "0": return
        print("Rendering background image")
        
        coords = self.master.coords
        center = [int((coords[0] + coords[2]+1)/2), int((coords[1] + coords[3]+1)/2)]
        scale = int(self.master.input.get_config("bgScale"))
        width = min(scale*(coords[2]-coords[0] + 10), center[0], self.page.img.size[0] - center[0] - 1)
        height = min(scale*(coords[3] - coords[1] + 10), center[1], self.page.img.size[1] - center[1] - 1)
        try:
            cv_img = np.array(np.array(self.page.img.crop(
                [center[0] - width, center[1] - height, center[0] + width, center[1] + height]
            ).convert('RGB'))[:, :, ::-1])
        except Exception as e:
            print("Failed to create mask base: " + str(e))
            return 
        cv2.rectangle(cv_img,
            (width + coords[0] - center[0], height + coords[1] - center[1]), 
            (width + coords[2] - center[0], height + coords[3] - center[1]), (255,255,255), -1)
        mask = np.zeros((height*2+2, width*2+2), np.uint8)
        flags = 4 | ( 255 << 8 ) | cv2.FLOODFILL_MASK_ONLY
        threshold = int(self.master.input.get_config("bgThreshold"))
        cv2.floodFill(cv_img, mask, (width, height), 255, (threshold,)*3, (threshold,)*3, flags)
        mask = mask[1:-1, 1:-1]
        contour ,hier = cv2.findContours(mask, cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contour:
            cv2.drawContours(mask,[cnt],0,255, -1)
        x,y,w,h = cv2.boundingRect(mask)
        mask = mask[y:y+h, x:x+w]
        temp = np.array(np.where(mask[:,:, np.newaxis] == [0], [0]*4, [255]*4), np.uint8)
        self.bounding_img = Image.fromarray(temp)
        self.bounding_img_tk = ImageTk.PhotoImage(self.page.resize_to_canvas(self.bounding_img))
        self.bounding_coords = [center[0] - width + x, center[1] - height + y]
        if update_coords:  
            ratio = 1.0 * min(height - y, y + h - height) / min(width - x, x + w - width)
            mask_center = [width - x, height - y]
            self.update_coords(mask, center, mask_center, ratio, recenter = 0)
        else:
            self.master.render()
    
        
    def update_coords(self, mask, center, mask_center, ratio, recenter = 0):
        coords = [mask_center[0] - 1, mask_center[1] - 1, mask_center[0]+1, mask_center[1]+1]
        h,w = mask.shape
        while True:
            if coords[0] <= 0 or coords[1] <= 0 or coords[2] >= w -1 or coords[3] >= h-1:
                break
            if 1.0*(coords[3] - coords[1])/(coords[2]-coords[0]) >= ratio:
                if not 0 in mask[coords[1]: coords[3],[coords[0]-1, coords[2] + 1]]:
                    coords[0] -= 1
                    coords[2] += 1
                else:
                    break
            else:
                if not 0 in mask[[coords[1]-1, coords[3]+1], coords[0]: coords[2]]:
                    coords[1] -= 1
                    coords[3] += 1
                else:
                    break
        
        self.master.update_coords([x + center[i%2] - mask_center[i%2] for i, x in enumerate(coords)])

    def render(self):
        if (not self.img or not self.text == self.master.input.get_text("finalText") or
            not " ".join([str(x) for x in self.padding]) == self.master.input.config["textPadding"].get()):
            self.text = self.master.input.get_text("finalText")
            self.make_img()
            self.border = 0
            
        border = int(self.master.input.config["textBorder"].get())
        if border > 0 and not border == self.border:
            self.border = border
            self.make_border()
        
        if self.bounding_img:
            self.canvas_bound = self.root.canvas.create_image(
                int(self.bounding_coords[0]*self.page.img_ratio),
                int(self.bounding_coords[1]*self.page.img_ratio), image=self.bounding_img_tk, anchor=tk.NW)
        self.render_text()
        
    def render_text(self):
        if self.canvas_img:
            self.root.canvas.delete(self.canvas_img)
            self.canvas_img = None
        self.canvas_img = self.root.canvas.create_image(
            self.master.input.coords[0], self.master.input.coords[1], image=self.tk_img, anchor=tk.NW)
        
        
    def make_img(self):
        print("Drawing text: " + self.text)
        
        words = list(filter(None, self.text.split(" ")))
        width = self.master.coords[2]-self.master.coords[0]
        height = self.master.coords[3]-self.master.coords[1]
        self.padding = list(map(int, self.master.input.config["textPadding"].get().split(" ")))
        text_width = width - self.padding[0] - self.padding[2]
        text_height = height - self.padding[1] - self.padding[3]
        self.img = Image.new('RGBA', [width, height], (255,255,255))
        ctx = ImageDraw.Draw(self.img)
        if len(words) == 0: 
            self.tk_img = ImageTk.PhotoImage(self.page.resize_to_canvas(self.img))
            return
        
        for font_size in range(int(self.master.input.get_config("maxFontSize")), 0, -1):
            try:
                font = ImageFont.truetype(font = self.master.input.get_config("fontPath"), size = font_size)  
            except OSError as e:
                print("Could not find specified font")
                self.tk_img = ImageTk.PhotoImage(self.page.resize_to_canvas(self.img))
                break   
                
            if max(list(map(lambda x: ctx.textsize(x, font = font)[0], words))) > text_width: 
                continue
            
            adjusted_text = words[0]
            for word in words[1:]:
                if ctx.textsize(adjusted_text + " " + word, font = font)[0] > text_width:
                    adjusted_text += "\n" + word
                else:
                    adjusted_text += " " + word
            
            adjusted_text = adjusted_text.strip().replace("_"," ")
            size = ctx.textsize(adjusted_text, font = font)
            if size[1] < text_height:
                xy = ((text_width-size[0])/2 + self.padding[0], (text_height-size[1])/2 + self.padding[1])
                ctx.text(xy, adjusted_text, font = font, fill=(0,0,0), align= "center")
                self.tk_img = ImageTk.PhotoImage(self.page.resize_to_canvas(self.img))
                break   
        
    def clear_background(self):
        self.bounding_img, self.bounding_img_tk, self.canvas_bound = None, None, None
        self.master.render()
        
        
    def hide(self):
        if self.canvas_img:
            self.root.canvas.delete(self.canvas_img)
            self.canvas_img = None
        if self.canvas_bound:
            self.root.canvas.delete(self.canvas_bound)
            self.canvas_bound = None
        
    def delete(self):
        self.hide()
        



        