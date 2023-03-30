# -*- coding: utf-8 -*-
"""
Created on Fri Mar  3 12:44:54 2023

@author: Matt Udakis
"""

import cv2
import numpy as np
import threading
import os 
import time
from datetime import datetime

import tkinter as tk
from tkinter import ttk  # Normal Tkinter.* widgets are not themed!
from tkinter import filedialog
from PIL import Image, ImageTk

from utils.app_classes import Rectangle
#from ttkthemes import ThemedTk


class video_stream():
    
    def __init__(self):
        self.frame = None
        self.running = False
        self.recording = False
        self.frame_resized = None
        self.tracked_position = None
        self.fps = 0
        self.colour_chan = 2
        self.led_thresh = 50
        self.video_resolution = [640,360]
        self.vid_tag = "Sample"


    def start_capture(self):
        vid_w = self.video_resolution[0]
        vid_h = self.video_resolution[1]
        
        self.capture = cv2.VideoCapture(0,cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, vid_w)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, vid_h)
        #self.capture.set(cv2.CAP_PROP_EXPOSURE, -3) # Setting the exposure on logitech cameras is often important as the frame rate drops if exposure is too high.
        #self.capture.set(cv2.CAP_PROP_SETTINGS, 0) # Use this to get camera settings for the webcam. (might include this into a menu option)
        # fourcc settings needs to be after all other settings for it to work?! - might be due to opencv backend being ffmpeg
        self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G")) # This is important to maintain higher FPS with higer resolution video
        
        frame_count = 0
        start = time.time()
        
        while self.running:
            self.ret, self.frame =  self.capture.read()

            if self.ret:
                frame_count += 1
                self.frame = cv2.flip(self.frame, 1)
                
                if self.recording:
                    self.video_writer.write(self.frame)
                
                now = time.time()
                frame_to_resize =  self.frame.copy()
                resize_factor = app.frame_resize_factor
                self.frame_resized = cv2.resize(frame_to_resize, 
                                               (int(frame_to_resize.shape[1] / resize_factor[1]),
                                                int(frame_to_resize.shape[0] / resize_factor[0]),
                                                ),)
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
        vid_name = (self.vid_tag+".avi")
        fourcc = cv2.VideoWriter_fourcc("M", "J", "P", "G")
        self.video_writer = cv2.VideoWriter(vid_name,fourcc , 30, (vid_w, vid_h))
        self.recording = True


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
            frame = self.frame_resized.copy()
            return frame
     
     
    def get_coords(self):   
        if self.tracked_position is not None:
            coords = np.array([(self.tracked_position)],dtype=int)
            return coords
    

    def find_position(self):
        kernel1 = np.ones((15,15),np.uint8)
        kernel2 = np.ones((6,6),np.uint8)
           
        frame_bw = cv2.cvtColor(self.frame_resized, cv2.COLOR_BGR2GRAY) # convert to black/white
        mask = cv2.subtract(self.frame_resized[:,:,self.colour_chan],frame_bw) #subtract BW frame from the selected colour channel
        (t, mask2) = cv2.threshold(mask, self.led_thresh, 255, cv2.THRESH_BINARY) #Threshold to get binary 
        mask2 = cv2.GaussianBlur(mask2,(3,3),0) #Add blur to smooth pixelation
        mask3 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel1) # using morphology close nearby pixels to get a 'blob'
        mask4 = cv2.dilate(mask3, kernel2) #dilate to make the blob bigger
        self.final_mask = mask4 
        
        #find the contours
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
        self.reward_zones = app.zones #get location of reward zones
        pos = self.tracked_position
        
        inzone = np.zeros(3,dtype=int)
        for i, zone in enumerate(self.reward_zones):
           inzone[i] = zone.is_occupied(pos)
           
        if any(inzone):
            zone_occupied = np.argwhere(inzone)
            zone_occupied = np.concatenate(zone_occupied,axis=None)
            zone_occupied = min(zone_occupied) #if there are multi zones occupied take the lowest one
            
            print(f"Zone {zone_occupied} occupied")
      
    
           
class tracker_app():
    def __init__(self,master):
        self.root = master
        self.root.title("LinearTrack_er")
        self.root.protocol("WM_DELETE_WINDOW", self.closeWindow)
        self.is_streaming = False
        self.led_threshold = 50
        self.mask_colour = [0,0,255]
        self.session_running = False
        self.rest_running = False
        self.session_start = 0
        self.session_number = 1
        self.display_resolution = [640*1.1, 360*1.1]
        self.possition_array = np.zeros((50,2),dtype=int)
        
        self.cam = video_stream() # create a video stream instance 
        self.setup_display() #setup the GUI
       

    def setup_display(self):
        """ Sets up the main GUI display with tkinter widgets
        """
        self.get_avaliable_resolutions()
        low_res = self.avaliable_resolutions[-1]
        
        self.capture = cv2.VideoCapture(0,cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, low_res[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, low_res[1])
        ret, frame =  self.capture.read()
        
        frame = cv2.flip(frame, 1)
        
        self.frame_resize_factor = [(low_res[0]/self.display_resolution[0]),(low_res[1]/self.display_resolution[1])]
        frame_resized = cv2.resize(frame, (int(frame.shape[1] / self.frame_resize_factor[1]),int(frame.shape[0] / self.frame_resize_factor[0]),),)
        
        #self.frame_resized = cv2.resize(frame_to_resize, (int(frame_to_resize.shape[1] / resize_factor[1]),int(frame_to_resize.shape[0] / resize_factor[0]),),)
        
        
        
        if ret:
            cv2image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGBA)
            last_frame = Image.fromarray(cv2image)
            tk_img = ImageTk.PhotoImage(image=last_frame)
    
        self.capture.release()
    
        viddims = frame_resized.shape[0:2]
       
        self.root.rowconfigure( (0,1), weight=1) 
        self.root.columnconfigure( (0,1), weight=1)  
       
        self.top_frame = ttk.Frame(self.root, height=viddims[0], width = 1000)
        self.top_frame.grid(row=0, column=0,sticky = 'nsew',padx=20, pady=(10,5))       
        self.top_frame.columnconfigure((0,1), weight=1)
        self.top_frame.rowconfigure((0,1), weight=1)
       
        self.video_frame = ttk.Frame(self.top_frame, width=self.display_resolution[0], height=self.display_resolution[1])
        self.video_frame.grid(row=0, column=0, rowspan=2)
        #self.video_frame.pack(fill="both", expand=True)
        
        self.video_canvas = tk.Canvas(self.video_frame, width=self.display_resolution[0], height=self.display_resolution[1],bd=0, highlightthickness=0, relief='ridge')
        self.video_canvas.tk_img = tk_img
        self.video_canvas.create_image(0,0, anchor=tk.NW, image=tk_img, tag='video')
        self.video_canvas.tag_lower('video','all')
        self.video_canvas.grid(row=0, column=0)
        
        r1 = Rectangle(self.video_canvas, 100, 170, 180, 250)
        r2 = Rectangle(self.video_canvas, 180, 190, 580, 230)
        r3 = Rectangle(self.video_canvas, 580, 170, 660, 250)

        self.zones = [r1, r2, r3]
        
        logo_img = Image.open("tktheme/theme/logos/trackerlogo.png")
        logo_img_small = logo_img.resize((220,40))
        self.logo_imgnew = ImageTk.PhotoImage(logo_img_small)
        
        logo_img_dark = Image.open("tktheme/theme/logos/trackerlogo_dark.png")
        logo_img_dark_small = logo_img_dark.resize((220,40))
        self.logo_imgnew_dark = ImageTk.PhotoImage(logo_img_dark_small)
        
        self.logo_canvas = tk.Canvas(self.top_frame , width= 220, height= 50)
        self.logo_canvas.logo_img = self.logo_imgnew_dark
        self.logo_canvas.create_image(5,5,anchor=tk.NW, image=self.logo_imgnew_dark)
        self.logo_canvas.grid(row=0, column=1, sticky = 'nsew', padx=(10),pady=(10))
        # Create a Label Widget to display the text or Image
        
        
        self.arduino_frame = ttk.Labelframe(self.top_frame,text='Arduino Control', height = 320, width = 200)
        self.arduino_frame.grid(row=1, column=1, padx=(10,5),pady=(5,0), sticky = 'nsew')
        
        
        
        self.bot_frame = ttk.Frame(self.root, height = 500, width = 1000)
        self.bot_frame.grid(row=1, column=0,sticky = 'nsew',padx=20, pady=(5,10))
        self.bot_frame.columnconfigure((0,1), weight=1)
        self.bot_frame.rowconfigure((0,1), weight=1)
        
        
        self.experiment_frame = ttk.Labelframe(self.bot_frame, text='Experiment Control', width = 330)
        self.experiment_frame.grid(row=0, column=2, rowspan=2, pady=(5,5), padx=(15,5), sticky = 'nsew')

        self.experiment_frame.columnconfigure((0,1), weight=1)
        self.experiment_frame.rowconfigure((0,1,2,3), weight=1)
        
        
        # start session button
        self.start_session_button = ttk.Checkbutton(
            self.experiment_frame, 
            text="Start Session", 
            style="Toggle.TButton", 
            command=self.start_stop_session_button
            )
        self.start_session_button.grid(
            row=0, 
            column=0, 
            padx=(50, 50), 
            pady=(30, 10),  
            sticky='nsew'
            )
        
        #start rest button
        self.start_rest_button = ttk.Checkbutton(
            self.experiment_frame,
            text="Start rest", 
            style="Toggle.TButton", 
            command=self.start_stop_rest_button
            )
        self.start_rest_button.grid(
            row=1, 
            column=0, 
            padx=(50, 50), 
            pady=(10, 10), 
            sticky='nsew'
            )
        
        # Frame to house session infomration
        self.sessions_frame = ttk.Frame(
            self.experiment_frame, 
            style='Card.TFrame'
            )
        self.sessions_frame.grid(
            row=2, 
            column=0, 
            rowspan=2, 
            sticky = 'nsew', 
            pady=(5,20), 
            padx=(20,10)
            )
        self.sessions_frame.columnconfigure((0,1), weight=1)
        self.sessions_frame.rowconfigure((0,1,2,3), weight=1)       
        
        #session number text and value
        self.session_number_label = tk.Label(
            self.sessions_frame,
            text = ("Session number: "),
            font=("Segoe Ui", 12)
            )
        self.session_number_label_val = tk.Label(
            self.sessions_frame,
            text = (str(self.session_number)),
            font=("Segoe Ui", 12),fg='#007fff'
            )
        self.session_number_label.grid(
            row=0, 
            column=0, 
            sticky = 'nsw', 
            pady=(10,5), 
            padx=(10,0)
            )
        self.session_number_label_val.grid(
            row=0, 
            column=1, 
            sticky = 'nsw', 
            pady=(10,5), 
            padx=(0,10)
            )
        
        # Lap number text and value
        self.lap_num_label = tk.Label(
            self.sessions_frame,
            text = "Number of laps:",
            font=("Segoe Ui", 12)
            )
        self.lap_num_label_val = tk.Label(
            self.sessions_frame,
            text = "0",
            font=("Segoe Ui", 12),
            fg='#007fff'
            )        
        self.lap_num_label.grid(
            row=1, 
            column=0, 
            sticky = 'nsw', 
            pady=(5,30), 
            padx=(10,0)
            )
        self.lap_num_label_val.grid(
            row=1, 
            column=1, 
            sticky = 'nsw', 
            pady=(5,30), 
            padx=(0,10)
            )       
        
        # Session Time text and value
        self.session_time_label = tk.Label(
            self.sessions_frame,
            text = "Session Time:",
            font=("Segoe Ui", 12)
            )
        self.session_time_label_val = tk.Label(
            self.sessions_frame,
            text = "00:00.0",
            font=("Segoe Ui", 12),
            fg='#007fff'
            )
        self.session_time_label.grid(
            row=2, 
            column=0, 
            sticky = 'nsw', 
            pady=(10,5), 
            padx=(10,0)
            )
        self.session_time_label_val.grid(
            row=2, 
            column=1, 
            sticky = 'nsw', 
            pady=(10,5), 
            padx=(0,10)
            )

        # Rest time text and value        
        self.rest_time_label = tk.Label(
            self.sessions_frame,
            text = "Rest Time:",
            font=("Segoe Ui", 12)
            )
        self.rest_time_label_val = tk.Label(
            self.sessions_frame,
            text = "00:00.0",
            font=("Segoe Ui", 12),
            fg='#007fff'
            )
        self.rest_time_label.grid(
            row=3, 
            column=0, 
            sticky = 'nsw', 
            pady=(5,10), 
            padx=(10,0)
            )
        self.rest_time_label_val.grid(
            row=3, 
            column=1, 
            sticky = 'nsw', 
            pady=(5,10), 
            padx=(0,10)
            )
        
        # Container to house session settings info
        self.sessions_settings_frame = ttk.Frame(
            self.experiment_frame,
            style='Card.TFrame'
            )
        self.sessions_settings_frame.grid(
            row=0, 
            column=1, 
            rowspan=3, 
            sticky = 'nsew', 
            pady=(10,10), 
            padx=(10,20)
            )   
        self.sessions_settings_frame.columnconfigure((0,1), weight=1)
        self.sessions_settings_frame.rowconfigure((0,1,2), weight=1)
       
       # Frame to house session, rest and ID length text and values
        self.length_frame = tk.Frame(self.sessions_settings_frame)
        self.length_frame.grid(
            column = 0, 
            row = 0, 
            columnspan=2, 
            pady=(5,5),
            padx=(5,5), 
            sticky = 'nsew'
            )           
        self.length_frame.columnconfigure((0,1), weight=1)
        self.length_frame.rowconfigure((0,1,2), weight=1)

        # Session length text and value
        self.session_length_label = tk.Label(
            self.length_frame,
            text = "Session Length:"
            )
        self.session_len = tk.IntVar(self.length_frame,10)
        self.session_length_input = ttk.Entry(
            self.length_frame,
            textvariable= self.session_len, 
            width = 5
            )
        self.session_length_label.grid(
            row=0, 
            column=0, 
            sticky = 'nsw', 
            pady=(5,0), 
            padx=(10,5)
            )
        self.session_length_input.grid(
            row=0, 
            column=1, 
            sticky = 'w', 
            pady=(5,5), 
            padx=(0,5)
            )
        
        # Rest length text and value
        self.rest_length_label = tk.Label(
            self.length_frame,
            text = "Rest Length:"
            )
        self.rest_len = tk.IntVar(self.length_frame,3)
        self.rest_length_input = ttk.Entry(
            self.length_frame,
            textvariable= self.rest_len, 
            width = 5
            )
        self.rest_length_label.grid(
            row=1, 
            column=0, 
            sticky = 'nsw', 
            pady=(5,5), 
            padx=(10,5)
            )
        self.rest_length_input.grid(
            row=1, 
            column=1, 
            sticky = 'w', 
            pady=(5,5), 
            padx=(0,5)
            )
        
        # Auto session length check box
        self.auto_session = tk.IntVar(value=0)
        self.auto_session_len = ttk.Checkbutton(
            self.length_frame, 
            variable=self.auto_session, 
            text = 'Auto session length'
            )
        self.auto_session_len.grid(
            row=2, 
            column=0,
            columnspan=2, 
            pady=5, 
            sticky='w', 
            padx=(10,5)
            )

        # Animal ID text and values
        self.animal_id_label = tk.Label(
            self.length_frame, 
            text = "Animal ID:"
            )
        self.animal_id = tk.StringVar(self.length_frame ,"#001")
        self.animal_id_input = ttk.Entry(
            self.length_frame,
            textvariable= self.animal_id, 
            width = 5
            )
        self.animal_id_label.grid(
            row=3, 
            column=0, 
            sticky = 'w', 
            pady=(15,10), 
            padx=(10,5)
            )
        self.animal_id_input.grid(
            row=3, 
            column=1, 
            sticky = 'w', 
            pady=(5,5), 
            padx=(0,5)
            )
        
        # Frame to house save settings
        self.saving_frame = tk.Frame(self.sessions_settings_frame)
        self.saving_frame.grid(
            column = 0, 
            row = 1, 
            columnspan=2, 
            pady=(0,5), 
            padx=(5,5), 
            sticky = 'nsew'
            )
        self.saving_frame.columnconfigure((0,1), weight=1)
        self.saving_frame.rowconfigure((0,1), weight=1)
        
        # Save directory input box 
        self.save_dir = tk.StringVar(self.saving_frame ,"C:/temp ")
        self.save_dir_input = ttk.Entry(
            self.saving_frame,
            textvariable= self.save_dir, 
            width = 12
            )
        self.save_dir_input.grid(
            row=1, 
            column=0, 
            columnspan=2, 
            sticky = 'nsew', 
            pady=(5,5), 
            padx=(10,10)
            )
        
        # Save directory get button 
        self.save_dir_button = ttk.Button(
            self.saving_frame,
            text="Get Save DIR", 
            command=self.get_save_dir
            )
        self.save_dir_button.grid(
            row=0, 
            column=0, 
            columnspan=2,  
            padx=(40, 30), 
            pady=(0, 5), 
            sticky='nsew'
            )
        
        # Frame for reset buttons
        self.reset_button_frame = tk.Frame(self.experiment_frame)
        self.reset_button_frame.grid(
            column = 1, 
            row = 3, 
            pady=(0,0), 
            sticky = 'nsew'
            )
        self.reset_button_frame.columnconfigure((0,1), weight=1)
        
        # Reset session button
        self.reset_sessions_button = ttk.Button(
            self.reset_button_frame,
            text="Reset\nSessions", 
            command=self.reset_sessions
            )
        self.reset_sessions_button.grid(
            row=0, 
            column=1,  
            padx=(5, 20), 
            pady=(10, 20),
            sticky='nsew'
            )
        
        # Reset rest button
        self.reset_experiment_button = ttk.Button(
            self.reset_button_frame,
            text="Reset\nExperiment", 
            command=self.reset_sessions
            )
        self.reset_experiment_button.grid(
            row=0, 
            column=0,  
            padx=(10, 5), 
            pady=(10, 20),
            sticky='nsew'
            )
        
        # Frame for Inscopix controls 
        self.inscopix_frame = ttk.Labelframe(
            self.bot_frame, 
            text='Inscopix Control',
            width = 300
            )
        self.inscopix_frame.grid(
            row=1, 
            column=1, 
            sticky = 'nsew', 
            pady=(10,5), 
            padx=(10,0)
            )
        
        
        # Frame for tracking controls
        self.tracking_frame = ttk.Labelframe(
            self.bot_frame,
            text='Tracking Controls', 
            height = 150, 
            width = 250
            )
        self.tracking_frame.grid(
            row=0, 
            column=0, 
            columnspan=2, 
            pady=5, 
            sticky = 'nsew'
            )   
        self.tracking_frame.columnconfigure((0,1,2), weight=1)
        self.tracking_frame.rowconfigure((0,1,2,3), weight=1)
        
        # Overlay tracking position checkbox
        self.overlay_position = tk.IntVar(value=0)
        self.overlay_check = ttk.Checkbutton(
            self.tracking_frame, 
            variable=self.overlay_position, 
            text = 'Overlay Position'
            )
        self.overlay_check.grid(
            row=2, 
            column=0, 
            pady=5, 
            sticky='nsew', 
            padx=(10,10)
            )
        
        # Save tracking data dialog box
        self.save_tracking = tk.IntVar(value=0)
        self.save_tracking_check = ttk.Checkbutton(
            self.tracking_frame, 
            variable=self.save_tracking, 
            text = 'Save Tracking Data', 
            state='selected'
            )
        self.save_tracking_check.grid(
            row=2, 
            column=1, 
            columnspan=2, 
            sticky='nsew', 
            pady=5, 
            padx=(0,10)
            )
        
        # LED colour threshold slider and label
        self.thresh_slider = ttk.Scale(
            self.tracking_frame, 
            length = 100, 
            from_=0, 
            to=100, 
            orient = 'horizontal', 
            command=self.update_led_thresh
            )
        self.thresh_slider.grid(
            row=0, 
            column=0, 
            columnspan=2, 
            sticky='ew', 
            padx=(20,0), 
            pady=(15,5)
            )
        self.thresh_slider.set(self.led_threshold)
        self.thresh_label = tk.Label(
            self.tracking_frame,
            text = "Red Threshold"
            )
        self.thresh_label .grid(
            row=0, 
            column=2,
            padx=5, 
            pady=(15,5), 
            sticky='w'
            )
       
        # LED mask size slider and label - probably not needed
        self.ledsize_slider = ttk.Scale(
            self.tracking_frame, 
            length = 100, 
            from_=0, 
            to=100, 
            orient = 'horizontal', 
            command=self.update_ledsize
            )
        self.ledsize_slider.grid(
            row=1, 
            column=0, 
            columnspan=2, 
            sticky='ew', 
            padx=(20,0),
            pady=5
            )
        self.ledsize_label = tk.Label(
            self.tracking_frame,
            text = "Red Size"
            )
        self.ledsize_label.grid(
            row=1, 
            column=2, 
            padx=5, 
            pady=5, 
            sticky='w'
            )

        # LED colour spinbox selector and label   
        self.colour_to_track = tk.StringVar()
        self.led_colour_spin = ttk.Spinbox(
            self.tracking_frame,
            textvariable=self.colour_to_track,
            width=12, 
            command=self.Led_to_track
            )
        self.led_colour_spin.grid(
            row=0, 
            column=3, 
            sticky='ew', 
            pady=(15,5), 
            padx=(5,0)
            )
        self.led_colour_spin['values'] = ('Red', 'Green', 'Blue')
        self.led_colour_spin['state'] = 'readonly'
        self.led_colour_spin.set('Red')
        self.led_label = tk.Label(
            self.tracking_frame,
            text = 'Tracking Colour'
            )
        self.led_label.grid(
            row=0, 
            column=4, 
            sticky='w', 
            padx=(5,20), 
            pady=(5,5)
            )
        
        # Display frame selector and label
        self.frame_to_display = tk.StringVar()
        self.frame_cb = ttk.Combobox(
            self.tracking_frame,
            textvariable=self.frame_to_display,
            width=12
            )
        self.frame_cb.grid(
            row=1, 
            column=3, 
            sticky='ew', 
            pady=(5,5), 
            padx=(5,0)
            )
        self.frame_cb['values'] = ('Track', 'led Mask', 'Crop Track')
        self.frame_cb['state'] = 'readonly'
        self.frame_cb.set('Track')
        self.frame_label = tk.Label(
            self.tracking_frame,
            text = 'Display Frame'
            )
        self.frame_label.grid(
            row=1, 
            column=4, 
            sticky='w', 
            padx=(5,20),
            pady=5
            )
        
        # Track crop button - could change to a checkbox
        self.crop_button = ttk.Button(
            self.tracking_frame,
            text="Crop Track",
            width=10
            )
        self.crop_button.grid(
            row=2, 
            column=3, 
            columnspan=2, 
            padx=(5,20), 
            sticky='sew', 
            pady=(5,20)
            )
        
        # Frame for aquisition controls
        self.aquisition_frame = ttk.Labelframe(
            self.bot_frame,
            text='Aquisition Control', 
            height = 140, 
            width = 150
            )
        self.aquisition_frame.grid(
            row=1, 
            column=0, 
            sticky = 'nsew', 
            pady=(10,5), 
            padx=(0,5)
            )
        self.aquisition_frame.columnconfigure((0,1), weight=1)  
        self.aquisition_frame.rowconfigure((0,1,2), weight=1)

        # Start and stop video stream button
        self.stream_but_state = tk.IntVar(value=0)
        self.stream_button = ttk.Checkbutton(
            self.aquisition_frame,
            text="Start Stream", 
            style="Toggle.TButton",
            variable =self.stream_but_state, 
            command=self.start_stop_stream_button
            )
        self.stream_button.grid(
            row=0, 
            column=0, 
            columnspan=2, 
            padx=(20, 20), 
            pady=(10, 10), 
            ipady=5,
            sticky='nsew'
            )
        
        # Start video recording button
        self.rec_but_state = tk.IntVar(value=0)
        self.start_button = ttk.Checkbutton(
            self.aquisition_frame,
            text="Record", 
            style="Toggle.TButton",
            variable = self.rec_but_state, 
            command=self.start_rec_button
            )
        self.start_button.grid(
            row=1, 
            column=0, 
            padx=(20,10), 
            pady=(5,20), 
            ipady=5,
            sticky='nsew'
            )
        
        # Stop video recording button
        self.stop_button = ttk.Button(
            self.aquisition_frame,
            text="Stop Rec.", 
            command=self.stop_rec_button, 
            state="disabled"
            )
        self.stop_button.grid(
            row=1, 
            column=1,
            padx=(10,20), 
            pady=(5,20), 
            ipady=5,
            sticky='nsew'
            )

        # Frame to hold video resolution and FPS
        self.vid_res_frame = ttk.Frame(self.aquisition_frame)
        self.vid_res_frame.grid(
            row=2, 
            column=0, 
            columnspan=2
            )
        
        # Video resolution selector spinbox
        self.video_res = tk.StringVar()
        self.vid_res_cb = ttk.Combobox(
            self.vid_res_frame,
            textvariable=self.video_res,
            height=5
            )
        self.vid_res_cb.grid(
            row=0, 
            column=1, 
            sticky='s', 
            pady=5, 
            padx=0
            )
        self.vid_res_cb['values'] = self.avaliable_resolutions_string
        self.vid_res_cb['state'] = 'readonly'
        self.vid_res_cb.set(self.avaliable_resolutions_string[-1])
    
        #self.set_camera_resolution()
        self.vid_res_cb.bind('<<ComboboxSelected>>', self.set_camera_resolution)
        self.vid_res_cb.bind("<<ComboboxSelected>>",lambda e: self.bot_frame.focus())
        
        self.fps_string_var = tk.StringVar()
        self.fps_label = tk.Label(
            self.vid_res_frame,
            textvariable = self.fps_string_var
            )
        self.fps_label.grid(
            row=0, 
            column=0, 
            sticky='w', 
            pady=2, 
            padx=2
            )
        
        
        self.theme_frame = ttk.Frame(self.bot_frame)
        self.theme_frame.grid(
            row=2, 
            column=2, 
            sticky = 'ne'
            )
        self.theme_switch = ttk.Checkbutton(
            self.theme_frame, 
            style='Switch.TCheckbutton', 
            text="Light", 
            command= self.change_theme
            )
        self.dark_label = tk.Label(self.theme_frame,text = 'Dark')
        #self.light_label = tk.Label(self.theme_frame,text = 'Light')
        
        self.dark_label.pack(side='left',padx=0, pady=0)
        self.theme_switch.pack(side='left',padx=(0,0), pady=0)
        self.root.iconbitmap("tktheme/theme/logos/tracker_icon.ico")

    
    
    def Led_to_track(self):
        led_colour = self.colour_to_track.get()
        self.ledsize_label['text'] = (led_colour + " Size")
        self.thresh_label['text'] = (led_colour + " Threshold")
        
        if led_colour == 'Red':
            channel = 2    
        elif led_colour == 'Green':
            channel = 1
        elif led_colour == 'Blue':
            channel = 0
        
        self.mask_colour = [0,0,0]
        self.mask_colour[channel] = 255
        self.cam.colour_chan = channel
        

    def change_theme(self):
        if self.root.tk.call("ttk::style", "theme", "use") == "azure-dark":
            # Set light theme
            self.root.tk.call("set_theme", "light")
            self.logo_canvas.delete('all')
            self.logo_canvas.logo_img = self.logo_imgnew
            self.logo_canvas.create_image(5,5,anchor=tk.NW, image=self.logo_imgnew)
        else:
            # Set dark theme
            self.root.tk.call("set_theme", "dark")
            self.logo_canvas.delete('all')
            self.logo_canvas.logo_img = self.logo_imgnew_dark
            self.logo_canvas.create_image(5,5,anchor=tk.NW, image=self.logo_imgnew_dark)


    def update_led_thresh(self,val):
        self.led_threshold = int(self.thresh_slider.get())
        self.cam.led_thresh = self.led_threshold
    

    def update_ledsize(self,val):
        self.ledSize = int(self.ledsize_slider.get())
    

    def get_save_dir(self):
        save_directory = filedialog.askdirectory()
        self.save_dir.set(save_directory)
        

    def reset_sessions(self):
        self.session_number = 1
        print(self.root.winfo_height())


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
        """ Sets video camera video resolution and 
            calculates resize factor for display frame  
        """        
        vid_res_index = self.vid_res_cb.current()
        camera_resolution = self.avaliable_resolutions[vid_res_index]
        
        self.cam.video_resolution = camera_resolution
        self.frame_resize_factor = [
                                   (camera_resolution[0]/self.display_resolution[0]),
                                   (camera_resolution[1]/self.display_resolution[1])
                                   ]
        
        
    def start_stop_session_button(self):
        """ Start/stop session timmer button 
        """
        if self.session_running: 
            print("stoping_session")
            self.start_session_button.config(text="Start Session")
            self.session_running = False
            self.session_number += 1
        else:
            self.session_start = datetime.now()
            print("starting session")
            self.start_session_button.config(text="Stop Session")
            self.session_running = True
         
    
    def start_stop_rest_button(self):
        """ Start/stop rest timmer button 
        """
        if self.rest_running: 
            print("stoping rest")
            self.start_rest_button.config(text="Start Rest")
            self.rest_running = False
        else:
            self.rest_start = datetime.now()
            print("starting rest")
            self.start_rest_button.config(text="Stop Rest")
            self.rest_running = True
    
    
    def start_stop_stream_button(self):
        """ Start/stop video stream button 
        """
        if self.cam.running:
            # Stop the video stream
            self.is_streaming = self.cam.stop_stream()
            
            # Update GUI buttons
            self.stream_button.config(text="Start Stream")
            self.stream_button.config(state="normal")
            self.rec_but_state.set(0)
            self.start_button.config(text="Record")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.vid_res_cb.config(state="readonly")
            
            return
        else:    
            # Start the video stream
            self.is_streaming = self.cam.start_stream()
            self.stream_button.config(text="Streaming... Press to stop")
            self.vid_res_cb.config(state="disabled")

        # if app is streaming, start display update loops
        if self.is_streaming:
            self.update_frame()
            self.refresher()
                
    
    def start_rec_button(self):         
        # start the video stream recording
        time_now = datetime.now()
        vid_time_stamp = time_now.strftime("%Y%m%d_%H%M%S")
        ID_stamp = self.animal_id.get()
        session_stamp = str(self.session_number)
        vidname = (ID_stamp + "_Session_" + session_stamp + "_" + vid_time_stamp)
        print("recording video: " + vidname)
        self.cam.vid_tag = vidname
        self.cam.start_record()
        
        # update the GUI buttons
        self.start_button.config(text="Recording...")
        self.start_button.config(state="disabled")
        self.stream_but_state.set(1)
        self.stream_button.config(text="Streaming... Press to stop")
        self.stop_button.config(state="normal")
        self.vid_res_cb.config(state="disabled")
        
        # if the video is not running start the stream
        if not self.cam.running:
            self.is_streaming = self.cam.start_stream()
        
        self.is_recording = True
        self.is_streaming = True

        # if the app is streaming video start display update loops
        if self.is_streaming:
            self.update_frame()
            self.refresher()
        

    def stop_rec_button(self):         
        self.is_recording = self.cam.stop_record()

        self.start_button.config(text="Record")
        self.rec_but_state.set(0)
        self.start_button.config(state="normal") 
        self.stop_button.config(state="disabled")
    

    def update_timers(self):
        if self.session_running:
            self.session_time = datetime.now() - self.session_start

            minutes, seconds = divmod(self.session_time.seconds, 60)
            hours, minutes = divmod(minutes, 60)
            hund_millis = round(self.session_time.microseconds/100000) 
            
            if hund_millis == 10:
                hund_millis = 0
            if hours > 0:
                session_time_string = f"{hours}:{minutes:02}:{seconds:02}.{hund_millis:01}"
            else:
                session_time_string = f"{minutes:02}:{seconds:02}.{hund_millis:01}"
                
            self.session_time_label_val['text'] = session_time_string
            self.session_number_label_val['text'] = (str(self.session_number))
        

        if self.rest_running:
            self.rest_time = datetime.now() - self.rest_start 
            
            minutes, seconds = divmod(self.rest_time.seconds, 60)
            hours, minutes = divmod(minutes, 60)
            hund_millis = round(self.rest_time.microseconds/100000) #Round the microseconds to hundreth-millisec.
            
            if hund_millis == 10:
                hund_millis = 0 
            if hours > 0:
                rest_time_string = f"{hours}:{minutes:02}:{seconds:02}.{hund_millis:01}"
            else:
                rest_time_string = f"{minutes:02}:{seconds:02}.{hund_millis:01}"
            
            self.rest_time_label_val['text'] = rest_time_string   
        
        
    def refresher(self):
        self.fps_string_var.set(f'FPS: {self.cam.fps:.2f}')
        
        if self.is_streaming:
            self.root.after(1000, self.refresher) # every second...    
    

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
                
            if self.frame_to_display.get() == 'LED Mask': 
                self.frame[self.cam.final_mask==255] = self.mask_colour
            
            cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
            self.last_frame = Image.fromarray(cv2image)
            tk_img = ImageTk.PhotoImage(image=self.last_frame)
            
            self.video_canvas.tk_img = tk_img
            self.video_canvas.create_image(0,0, anchor=tk.NW, image=tk_img, tag='video')
            self.video_canvas.tag_lower('video','all')
            
        self.update_timers()

        if self.is_streaming:
            self.root.after(10, self.update_frame)
            

    def closeWindow(self):
        self.cam.stop_stream()
        self.root.destroy()


   
if __name__ == "__main__":
    
    root = tk.Tk()
    
    dir_path = os.path.dirname(os.path.realpath(__file__))
    root.tk.call('source', os.path.join(dir_path, 'tktheme\\azure.tcl'))
    root.tk.call("set_theme", "dark")
    style = ttk.Style()
    style.configure('TCombobox', selectbackground=None, selectforeground=None)
    
    app = tracker_app(root)
    
    # update the window and then set the min size for the window to keep geometry
    root.update()
    root.minsize(root.winfo_width(), root.winfo_height())
    x_cordinate = int((root.winfo_screenwidth() / 2) - (root.winfo_width() / 2))
    y_cordinate = int((root.winfo_screenheight() / 2) - (root.winfo_height() / 2))
    root.geometry("+{}+{}".format(x_cordinate, y_cordinate-20))
    
    root.mainloop()

    
    
