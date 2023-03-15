# -*- coding: utf-8 -*-
"""
Created on Fri Mar  3 12:44:54 2023

@author: Matt Udakis
"""

import cv2
import numpy as np
import threading
import tkinter as tk
from PIL import Image, ImageTk
from utils.app_classes import Rectangle
import os 
import time

from tkinter import ttk  # Normal Tkinter.* widgets are not themed!
#from ttkthemes import ThemedTk



class video_stream():
    def __init__(self):
        self.frame = None
        self.running = False
        self.recording = False
        self.frame_resized = None
        self.tracked_position = None
        self.fps = 0
        
        
        
        self.video_resolution = [640,360]
        print("this is the updated video resolution: ", self.video_resolution)    
   

    
    
    def start_capture(self):
        
        print("this is the updated video resolution: ", self.video_resolution)
        
        vid_w = self.video_resolution[0]
        vid_h = self.video_resolution[1]
        
        self.capture = cv2.VideoCapture(0,cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_SETTINGS, 0) #Use this to get camera settings for the webcam. (might include this into a menu option)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, vid_w)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, vid_h)
        #self.capture.set(cv2.CAP_PROP_EXPOSURE, -3) # Setting the exposure on logitech cameras is often important as the frame rate drops if exposure is too high.
            
        
        self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G")) # This is important to maintain higher FPS with higer resolution video
        # bizarrely the fourcc settings needs to be after all other settings for it to work?! - might be due to opencv backend being ffmpeg
        
        # if self.recording:
        #     vidname = "test"
        #     fourcc = cv2.VideoWriter_fourcc("M", "J", "P", "G")
        #     self.video_writer = cv2.VideoWriter("sample.avi",fourcc , 30, (vid_w, vid_h))
        
        frame_count = 0
        start = time.time()
        while self.running:
            self.rect, self.frame =  self.capture.read()
            
            if self.rect:
                frame_count += 1
                self.frame = cv2.flip(self.frame, 1)
                
                if self.recording:
                    self.video_writer.write(self.frame)
                
                now = time.time()
                frame_to_resize =  self.frame.copy()
                resize_factor = app.frame_resize_factor
                self.frame_resized = cv2.resize(frame_to_resize, (int(frame_to_resize.shape[1] / resize_factor[1]),int(frame_to_resize.shape[0] / resize_factor[0]),),)
                
                
                self.find_position()
                self.process_position()
                
                self.elapsed = now-start
                self.fps = round(frame_count / self.elapsed,2)
                
              
          
        self.capture.release()
        #self.video_writer.release()
        
        return
    
    def start_stream(self):
            
        self.running = True
        self.thread = threading.Thread(target=self.start_capture, daemon=True)
        self.thread.start()
        #self.update_frame()
        return True
    
    def start_record(self):
         
        
        
        vid_w = self.video_resolution[0]
        vid_h = self.video_resolution[1]
        vidname = "test"
        fourcc = cv2.VideoWriter_fourcc("M", "J", "P", "G")
        self.video_writer = cv2.VideoWriter("sample.avi",fourcc , 30, (vid_w, vid_h))
        
        self.recording = True
        
        #return True
    
    def stop_record(self):
        
        if self.recording:
            self.recording = False
            self.video_writer.release()

        return False        
            
        
    def stop_stream(self):
        
        self.running = False
        
        if self.recording:
            self.recording = False
            self.video_writer.release()

        return False
    

    def get_frame(self):
        
        if self.frame_resized is not None:
            
            #frame = self.frame_toshare
            frame = self.frame_resized.copy()
            return frame
    def get_mask(self):
        
        if self.frame_resized is not None:
            
            #frame = self.frame_toshare
            frame = self.frame_resized.copy()
            return frame
    
    def get_coords(self):
        
        if self.tracked_position is not None:
            
            coords = np.array([(self.tracked_position)],dtype=int)
            return coords
    
    def find_position(self):
            
        self.redThresh = app.redThreshold
        
        
        kernel1 = np.ones((15,15),np.uint8)
        kernel2 = np.ones((6,6),np.uint8)
           
        frame_bw = cv2.cvtColor(self.frame_resized, cv2.COLOR_BGR2GRAY)
        mask = cv2.subtract(self.frame_resized[:,:,2],frame_bw) 
        (t, mask2) = cv2.threshold(mask, self.redThresh, 255, cv2.THRESH_BINARY)
        # using morphology close nearby pixels to get a 'blob'
       
        mask2 = cv2.GaussianBlur(mask2,(3,3),0)
       
        mask3 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel1)
        mask4 = cv2.dilate(mask3, kernel2) #dilate to make the blob bigger
        self.final_mask = mask4
       
        #mask5 = cv2.bitwise_and(mask4, mask4, mask=trackmask)
        # find the contours red
        contours, hierarchy = cv2.findContours(self.final_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
       
       
        # find contour with max area   
        try:
            c = max(contours, key = cv2.contourArea)
            # using moments find the centroid of that contour
            M = cv2.moments(c)
            x = int(M['m10']/M['m00'])
            y = int(M['m01']/M['m00'])
        except:    
            x = 0
            y = 0
       
        self.tracked_position = [x,y]
          
          
      
    def process_position(self):
        
        self.reward_zones = app.zones
        
        pos = self.tracked_position
        
        inzone = np.zeros(3,dtype=int)
        for i, r in enumerate(self.reward_zones):
           inzone[i] = r.is_occupied(pos)
           
        #print(inzone)
        if any(inzone):
            zone_occupied = np.argwhere(inzone)
            zone_occupied = np.concatenate(zone_occupied,axis=None)
            zone_occupied = min(zone_occupied) #if there are multi zones occupied take the lowest one
            
            print(f"Zone {zone_occupied} occupied")
      
    
    
    
    
        
            
            
class Tracker_app():
    def __init__(self,master):
       self.root = master
       self.root.title("Resizable Rectangles")
       self.root.geometry('1200x900')
       self.root.protocol("WM_DELETE_WINDOW", self.closeWindow)
       self.is_streaming = False
       self.redThreshold = 50
       #self.fps_string_var = "text"
       self.display_resolution = [640*1.2, 360*1.2]
       self.possition_array = np.zeros((50,2),dtype=int)
       
       self.cam = video_stream() 
    
       self.setup_display()
       

        
    
        
    def setup_display(self):
        
       
        
       self.get_avaliable_resolutions()
       low_res = self.avaliable_resolutions[-1]
       
       
       self.capture = cv2.VideoCapture(0,cv2.CAP_DSHOW)
       self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, low_res[0])
       self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, low_res[1])
       rect, frame =  self.capture.read()
       
       frame = cv2.flip(frame, 1)
       
       #[(camera_resolution[0]/self.display_resolution[0]),(camera_resolution[1]/self.display_resolution[1])]
       
       self.frame_resize_factor = [(low_res[0]/self.display_resolution[0]),(low_res[1]/self.display_resolution[1])]
       frame_resized = cv2.resize(frame, (int(frame.shape[1] / self.frame_resize_factor[1]),int(frame.shape[0] / self.frame_resize_factor[0]),),)
       
       #self.frame_resized = cv2.resize(frame_to_resize, (int(frame_to_resize.shape[1] / resize_factor[1]),int(frame_to_resize.shape[0] / resize_factor[0]),),)
       
       
       
       if rect:
           cv2image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGBA)
           last_frame = Image.fromarray(cv2image)
           tk_img = ImageTk.PhotoImage(image=last_frame)
    
       self.capture.release()
    
       viddims = frame_resized.shape[0:2]
       
       
       
       self.top_frame = ttk.Frame(self.root, height=viddims[0], width = 1200)
       self.top_frame.pack(anchor='nw', padx=20, pady=(20,5))
       
       
       self.top_frame.columnconfigure(0, weight=1)
       self.top_frame.columnconfigure(1, weight=2)

       self.top_frame.rowconfigure(0, weight=1)
       
       self.video_frame = ttk.Frame(self.top_frame, width=viddims[1], height=viddims[0])
       self.video_frame.grid(row=0, column=0)
       #self.video_frame.pack(fill="both", expand=True)
       
       
       self.video_canvas = tk.Canvas(self.video_frame, width=self.display_resolution[0], height=self.display_resolution[1],bd=0, highlightthickness=0, relief='ridge')
       self.video_canvas.tk_img = tk_img
       self.video_canvas.create_image(0,0, anchor=tk.NW, image=tk_img, tag='video')
       self.video_canvas.tag_lower('video','all')
       self.video_canvas.pack()
       
    
       r1 = Rectangle(self.video_canvas, 20, 200, 100, 280)
       r2 = Rectangle(self.video_canvas, 100, 220, 500, 260)
       r3 = Rectangle(self.video_canvas, 500, 200, 580, 280)
    
       self.zones = [r1, r2, r3]
    
       self.update_frame() 
       
       
       self.arduino_frame = ttk.Labelframe(self.top_frame,text='Arduino Control', height = 350, width = 250)
       #self.arduino_frame.pack(anchor='ne', fill="both", expand=True)
       self.arduino_frame.grid(row=0, column=1, padx=20, sticky = 's')
       
       
       self.bot_frame = ttk.Frame(self.root, height = 500, width = 1200)
       self.bot_frame.pack(anchor='sw',padx=20, pady=(5,10))
       
       self.experiment_frame = ttk.Labelframe(self.bot_frame, text='Experiment Control', width = 330)
       self.experiment_frame.grid(row=0, column=3, rowspan=2, pady=(5,10), padx=(20,5), sticky = 'nsew')
       
       self.inscopix_frame = ttk.Labelframe(self.bot_frame, text='Inscopix Control',width = 220)
       self.inscopix_frame.grid(row=1, column=1, sticky = 'nsew', pady=(10,10), padx=(10,0))
       
       
       # self.bot_frame.columnconfigure(0, weight=1)
       # self.bot_frame.columnconfigure(1, weight=1)

       # self.bot_frame.rowconfigure(0, weight=2)
       # self.bot_frame.rowconfigure(1, weight=1)
       
       self.tracking_frame = ttk.Labelframe(self.bot_frame,text='Tracking Controls', height = 150, width = 498)
       self.tracking_frame.grid(row=0, column=0, columnspan=2, pady=5, sticky = 'nw')
       
       
       self.tracking_frame.columnconfigure(0, weight=1)
       self.tracking_frame.columnconfigure(1, weight=1)
       self.tracking_frame.columnconfigure(2, weight=1)

       self.tracking_frame.rowconfigure(0, weight=1)
       self.tracking_frame.rowconfigure(1, weight=1)
       self.tracking_frame.rowconfigure(2, weight=1)
       self.tracking_frame.rowconfigure(3, weight=1)
       
       self.overlay_position = tk.IntVar(value=0)
       self.overlay_check = ttk.Checkbutton(self.tracking_frame, variable=self.overlay_position, text = 'Overlay Position')
       self.overlay_check.grid(row=2, column=0, pady=5, sticky='n', padx=(5,0))
       
       self.save_tracking = tk.IntVar(value=0)
       self.save_tracking_check = ttk.Checkbutton(self.tracking_frame, variable=self.save_tracking, text = 'Save Tracking Data', state='selected')
       self.save_tracking_check.grid(row=2, column=1, columnspan=2, sticky='nw', pady=5, padx=(0,10))
       
     
      
       
       #red_thresh = tk.IntVar()
       self.redthresh_slider = ttk.Scale(self.tracking_frame, length = 200, from_=0, to=100, orient = 'horizontal', command=self.update_redthresh)
       self.redthresh_slider.set(self.redThreshold)
       self.redthresh_slider.grid(row=0, column=0, columnspan=2, sticky='e', padx=(20,0), pady=(15,5))
       self.redthresh_label = tk.Label(self.tracking_frame,text = 'Red Threshold')
       self.redthresh_label .grid(row=0, column=2,padx=5, pady=(15,5), sticky='w')
       #self.redthresh_label
       
       self.redsize_slider = ttk.Scale(self.tracking_frame, length = 200, from_=0, to=100, orient = 'horizontal', command=self.update_redsize)
       self.redsize_slider.grid(row=1, column=0, columnspan=2, sticky='e', padx=(20,0),pady=5)
       self.redsize_label = tk.Label(self.tracking_frame,text = 'Red Size')
       self.redsize_label.grid(row=1, column=2, padx=5, pady=5, sticky='w')
       
       
      
       self.colour_to_track = tk.StringVar()
       self.LED_colour_spin = ttk.Spinbox(self.tracking_frame,textvariable=self.colour_to_track,width=12)
       self.LED_colour_spin.grid(row=0, column=3, sticky='ew', pady=(15,5), padx=(15,0))
       self.LED_colour_spin['values'] = ('Red', 'Green', 'Blue')
       self.LED_colour_spin['state'] = 'readonly'
       self.LED_colour_spin.set('Red')
       self.led_label = tk.Label(self.tracking_frame,text = 'Tracking Colour')
       self.led_label.grid(row=0, column=4, sticky='w', padx=(5,20), pady=(15,5))
       
       self.frame_to_display = tk.StringVar()
       self.frame_cb = ttk.Combobox(self.tracking_frame,textvariable=self.frame_to_display,width=12)
       self.frame_cb.grid(row=1, column=3, sticky='ew', pady=(5,5), padx=(15,0))
       self.frame_cb['values'] = ('Track', 'Red Mask', 'Crop Track')
       self.frame_cb['state'] = 'readonly'
       self.frame_cb.set('Track')
       self.frame_label = tk.Label(self.tracking_frame,text = 'Display Frame')
       self.frame_label.grid(row=1, column=4, sticky='w', padx=(5,20),pady=5)
       
       self.crop_button = ttk.Button(self.tracking_frame,text="Crop Track",width=10)
       self.crop_button.grid(row=2, column=3, columnspan=2, padx=(15,20), sticky='sew', pady=(5,20))
       
       
       
       self.aquisition_frame = ttk.Labelframe(self.bot_frame,text='Aquisition Control', height = 140, width = 244)
       self.aquisition_frame.grid(row=1, column=0, sticky = 'nw', pady=(10,10), padx=(0,5))
       
       self.stream_button = ttk.Button(self.aquisition_frame,text="Start Stream", command=self.start_stop_stream_button)
       self.stream_button.grid(row=0, column=0, columnspan=2, padx=(20, 20), pady=(10, 10), ipadx=38, ipady=7)
      
       self.start_button = ttk.Button(self.aquisition_frame,text="Record", command=self.start_rec_button)
       self.start_button.grid(row=1, column=0, padx=(30,10), pady=(5,20), ipadx=10, ipady=7,sticky='n')
       
       self.stop_button = ttk.Button(self.aquisition_frame,text="Stop Rec.", command=self.stop_rec_button, state="disabled")
       self.stop_button.grid(row=1, column=1,padx=(10,30), pady=(5,20), ipadx=10, ipady=7)
       
       
       self.video_res = tk.StringVar()
       self.vid_res_cb = ttk.Combobox(self.aquisition_frame,textvariable=self.video_res,height=5)
       
       self.vid_res_cb.grid(row=2, column=0, columnspan=2, sticky='s', pady=5, padx=0)
       self.vid_res_cb['values'] = self.avaliable_resolutions_string
       self.vid_res_cb['state'] = 'readonly'
       self.vid_res_cb.set(self.avaliable_resolutions_string[-1])
       self.set_camera_resolution()
       self.vid_res_cb.bind('<<ComboboxSelected>>', self.set_camera_resolution)
       self.vid_res_cb.bind("<<ComboboxSelected>>",lambda e: self.bot_frame.focus())
       
       self.fps_string_var = tk.StringVar()
       self.fps_label = tk.Label(self.aquisition_frame,textvariable = self.fps_string_var).grid(row=2, column=0, sticky='w', pady=2, padx=2)
       
       self.theme_frame = ttk.Frame(self.bot_frame)
       self.theme_frame.grid(row=1, column=4, sticky = 'sw', pady=(10))
       self.theme_switch = ttk.Checkbutton(self.theme_frame, style='Switch_vert.TCheckbutton', command= self.change_theme,)
       self.dark_label = tk.Label(self.theme_frame,text = 'Dark')
       self.light_label = tk.Label(self.theme_frame,text = 'Light')
       
       self.dark_label.pack(side='top',padx=0, pady=0)
       self.theme_switch.pack(side='top',padx=(4,0), pady=0)
       self.light_label.pack(side='top',padx=0, pady=0)
       
    def change_theme(self):
        if self.root.tk.call("ttk::style", "theme", "use") == "azure-dark":
            # Set light theme
            self.root.tk.call("set_theme", "light")
        else:
            # Set dark theme
            self.root.tk.call("set_theme", "dark")
            
    def update_redthresh(self,val):
        self.redThreshold = int(self.redthresh_slider.get())
    
    
    def update_redsize(self,val):
        self.redSize = int(self.redsize_slider.get())
    
    
    def update_greenthresh(self,val):
        self.greenThreshold = int(self.greenthresh_slider.get())
    
    
    def update_greensize(self,val):
        self.greenSize = int(self.greensize_slider.get())
       
    
    def get_avaliable_resolutions(self):   
       
        possible_res = [(1920, 1080), (1280,720), (854,480), (640,360)]
        self.avaliable_resolutions = []
        for res in possible_res: 
            
            capture = cv2.VideoCapture(0,cv2.CAP_DSHOW)
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, res[0])
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, res[1])
            
            h = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            w = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            #print("got this height:",h)
            #print("got this width:",w)
            if h % 12 == 0 and w % 16 == 0: #check to see if it fits standard 16:9 resolution scale
                resolution = [int(w),int(h)]
                if resolution not in self.avaliable_resolutions:
                    self.avaliable_resolutions.append(resolution)            
            
        capture.release()
        
        self.avaliable_resolutions_string = []
        for i in self.avaliable_resolutions:
            resolution_str = (str(i[1])+"p " + "("+str(i[0])+"x"+str(i[1])+")")
            self.avaliable_resolutions_string.append(resolution_str)
        
        
    
    def set_camera_resolution(self,*args):
        
        vid_res_index = self.vid_res_cb.current()
        camera_resolution = self.avaliable_resolutions[vid_res_index]
        
        self.cam.video_resolution = camera_resolution
        self.frame_resize_factor = [(camera_resolution[0]/self.display_resolution[0]),(camera_resolution[1]/self.display_resolution[1])]
        
        
    
    
    
    def start_stop_stream_button(self):
        
        
        if self.cam.running:
            self.is_streaming = self.cam.stop_stream()
            
            self.stream_button.config(text="Start Stream")
            self.stream_button.config(state="normal")
            self.start_button.config(text="Record")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.vid_res_cb.config(state="readonly")
            
            return
            
        self.is_streaming = self.cam.start_stream()
        self.stream_button.config(text="Streaming... Press to stop")
        self.vid_res_cb.config(state="disabled")
        
        
        if self.is_streaming:
            self.update_frame()
            self.Refresher()
                
    
    
    def start_rec_button(self):   
        
        self.cam.start_record()
        
        self.start_button.config(text="Recording...")
        self.start_button.config(state="disabled")
        self.stream_button.config(text="Streaming... Press to stop")
        self.stop_button.config(state="normal")
        self.vid_res_cb.config(state="disabled")
        
        if not self.cam.running:
            self.is_streaming = self.cam.start_stream()
        
        self.is_recording = True
        self.is_streaming = True
        
        
        if self.is_streaming:
            self.update_frame()
            self.Refresher()
        
    def stop_rec_button(self):
        
         
        self.is_recording = self.cam.stop_record()
        
        self.start_button.config(text="Record")
        self.start_button.config(state="normal") 
        self.stop_button.config(state="disabled")
    

        
        
        
    def Refresher(self):
    
        self.fps_string_var.set(("FPS: " + str(self.cam.fps)))
        
        if self.is_streaming:
            
            self.root.after(1000, self.Refresher) # every second...    
    
    def get_tracked_data(self):
        
        coords = self.cam.get_coords()
        self.possition_array = np.append(coords,self.possition_array[0:-1,:],axis=0)
       
        return self.possition_array 
    
    def update_frame(self):
        
        self.frame = self.cam.get_frame()
        self.coords = self.cam.get_coords()
        if self.frame is not None:
            
            if self.overlay_position.get():
                possition_data = self.get_tracked_data()
                for pos in possition_data:
                    center = (pos[0],pos[1])
                    radius = 4
                    width = 1
                    self.frame = cv2.circle(self.frame, center, radius, (0, 0, 255), width)
                
            if self.frame_to_display.get() == 'Red Mask': 
                self.frame[self.cam.final_mask==255] = (0, 0, 255)
            
            
            cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
    
            
            self.last_frame = Image.fromarray(cv2image)
            tk_img = ImageTk.PhotoImage(image=self.last_frame)
            
            self.video_canvas.tk_img = tk_img
            self.video_canvas.create_image(0,0, anchor=tk.NW, image=tk_img, tag='video')
            self.video_canvas.tag_lower('video','all')
            
            
        
        
        
        
        if self.is_streaming:
            
            self.root.after(10, self.update_frame)
            


    def closeWindow(self):
        self.cam.stop_stream()
        self.root.destroy()



#def main():

    
if __name__ == "__main__":
    
    #root = ThemedTk(theme="equilux",themebg = True)
    #root.configure(bg="#293137")
    root = tk.Tk()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    root.tk.call('source', os.path.join(dir_path, 'tktheme\\azure.tcl'))
    root.tk.call("set_theme", "dark")
    style = ttk.Style()
    style.configure('TCombobox', selectbackground=None, selectforeground=None)
    
    app = Tracker_app(root)
    root.mainloop()

    
    
