# -*- coding: utf-8 -*-
"""
Created on Tue Mar  7 17:39:18 2023

@author: mu16645
"""

class Rectangle:
    def __init__(self, canvas, x1, y1, x2, y2):
        self.canvas = canvas
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.id = canvas.create_rectangle(x1, y1, x2, y2, width=2, outline="red",activefill='#007fff')
        self.active = False
        self.selected_corner = None
        self.canvas.tag_bind(self.id, '<Button-1>', self.on_button_press)
        self.canvas.tag_bind(self.id, '<Button1-Motion>', self.on_move_press)
        self.canvas.tag_bind(self.id, "<ButtonRelease-1>", self.on_button_release)
    
    def on_button_press(self, event):
        if self.is_inside(event):
            self.active = True
            self.canvas.tag_raise(self.id)
            self.start = event
            self.offset_x = event.x - self.canvas.coords(self.id)[0]
            self.offset_y = event.y - self.canvas.coords(self.id)[1]
            self.selected_corner = self.get_selected_corner(event)
            print(self.canvas.coords(self.id))
            
    def get_bounds(self):
            return self.canvas.bbox(self.id)
        
    def is_occupied(self, pos):
        x = pos[0]
        y = pos[1]
        bbox = self.canvas.bbox(self.id)
        return bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]
    
    def on_button_release(self, event):
        self.active = False
        self.selected_corner = None
    
    def on_move_press(self, event):
        if self.active and self.selected_corner == None:
            x, y = event.x, event.y  
            dx  = x - self.offset_x - self.canvas.coords(self.id)[0]
            dy  = y - self.offset_y - self.canvas.coords(self.id)[1]
            
            x1 = self.canvas.coords(self.id)[0] 
            y1 = self.canvas.coords(self.id)[1]
            x2 = self.canvas.coords(self.id)[2]
            y2 = self.canvas.coords(self.id)[3]
            
            x1new = x1 + dx
            y1new = y1 + dy
              
            h = self.canvas.winfo_height()
            w = self.canvas.winfo_width()
            
            if (1 < x1new < w-(x2-x1)) & (1 < y1new < h-(y2-y1)):
                self.canvas.move(self.id,dx,dy)


        if self.active and self.selected_corner:
            x1, y1 = event.x, event.y
            if self.selected_corner == "top_left":
                self.canvas.coords(self.id, x1, y1, self.canvas.coords(self.id)[2], self.canvas.coords(self.id)[3])
            elif self.selected_corner == "top_right":
                self.canvas.coords(self.id, self.canvas.coords(self.id)[0], y1, x1, self.canvas.coords(self.id)[3])
            elif self.selected_corner == "bottom_left":
                self.canvas.coords(self.id, x1, self.canvas.coords(self.id)[1], self.canvas.coords(self.id)[2], y1)
            elif self.selected_corner == "bottom_right":
                self.canvas.coords(self.id, self.canvas.coords(self.id)[0], self.canvas.coords(self.id)[1], x1, y1)
    
    def is_inside(self, event):
        x, y = event.x, event.y
        bbox = self.canvas.bbox(self.id)
        return bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]
    
    def get_selected_corner(self, event):
        corner_dims = 10
        x, y = event.x, event.y
        bbox = self.canvas.bbox(self.id)
        if bbox[0] <= x <= bbox[0]+corner_dims and bbox[1] <= y <= bbox[1]+corner_dims:
            return "top_left"
        elif bbox[2]-corner_dims <= x <= bbox[2] and bbox[1] <= y <= bbox[1]+corner_dims:
            return "top_right"
        elif bbox[0] <= x <= bbox[0]+corner_dims and bbox[3]-corner_dims <= y <= bbox[3]:
            return "bottom_left"
        elif bbox[2]-corner_dims <= x <= bbox[2] and bbox[3]-corner_dims <= y <= bbox[3]:
            return "bottom_right"
        else:
            return None