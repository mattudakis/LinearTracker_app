# -*- coding: utf-8 -*-
"""
Created on Tue Mar  7 17:39:18 2023

@author: mu16645
"""

class Rectangle:
    def __init__(self, canvas, coordinates, name):
        
        self.canvas = canvas
        self.coords = self.validate_input(coordinates)
        self.name = name
        self.base_colour = '#3cdfff'
        self.x1 = self.coords[0]
        self.y1 = self.coords[1]
        self.x2 = self.coords[2]
        self.y2 = self.coords[3]
        self.id = canvas.create_rectangle(self.x1, self.y1, self.x2, self.y2, width=1.5, outline=self.base_colour, activedash=(7,),activewidth = 5)
        self.active = False
        self.selected_corner = None
        self.canvas.tag_bind(self.id, '<Button-1>', self.on_button_press)
        self.canvas.tag_bind(self.id, '<Button1-Motion>', self.on_move_press)
        self.canvas.tag_bind(self.id, "<ButtonRelease-1>", self.on_button_release)
    
    def validate_input(self,input):
        if len(input)<4 or len(input)>4:
            raise ValueError("coordinates must be a list/array with 4 integers x1, y1, x2, y2")
        
        if all(isinstance(x, int) for x in input):
            return input
        else: 
            raise ValueError("coordinates must be integers")

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
    

class RewardZone(Rectangle):
    def __init__(self, canvas, coordinates, rewardport, name):

        self.rewardport = rewardport
        self.isactive = True
        super().__init__(canvas, coordinates, name)
    
    def change_colour(self, colour):
        self.canvas.itemconfig(self.id, outline=colour)

    def deactivate(self):
        self.change_colour('red')
        self.isactive = False

    def activate(self):
        self.change_colour(self.base_colour)
        self.isactive = True
