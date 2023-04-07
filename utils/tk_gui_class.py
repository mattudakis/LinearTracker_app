"""
GUI view 

Class for the the GUI for the linear Tracker app 
"""


import numpy as np
import cv2
import threading
import os 
import time
from datetime import datetime

import tkinter as tk
from tkinter import ttk  # Normal Tkinter.* widgets are not themed!
from tkinter import filedialog
from PIL import Image, ImageTk
from utils.app_classes import Rectangle



class tk_gui():
    def __init__(self,master):
        self.root = master
        self.root.title("LinearTrack_er")
        
        self.display_resolution = [640*1.1, 360*1.1]
        self.is_streaming = False
        self.led_threshold = 50
        self.mask_colour = [0,0,255]
        self.session_running = False
        self.rest_running = False
        self.session_start = 0
        self.session_number = 1
        self.setup_display()


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
            style="Toggle.TButton" 
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
            text="Get Save DIR"
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
            text="Reset\nSessions" 
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
            text="Reset\nExperiment"
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
            orient = 'horizontal'
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
            orient = 'horizontal'
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
            width=12
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
        self.frame_cb['values'] = ('Track', 'LED Mask', 'Crop Track')
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
            variable =self.stream_but_state
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
            variable = self.rec_but_state
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
            text="Light"
            )
        self.dark_label = tk.Label(self.theme_frame,text = 'Dark')
        #self.light_label = tk.Label(self.theme_frame,text = 'Light')
        
        self.dark_label.pack(side='left',padx=0, pady=0)
        self.theme_switch.pack(side='left',padx=(0,0), pady=0)
        self.root.iconbitmap("tktheme/theme/logos/tracker_icon.ico")
        
    
    
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