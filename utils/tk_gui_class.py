"""
GUI view 

Class for the the GUI for the linear Tracker app 
"""

import cv2
import tkinter as tk
from tkinter import ttk  
from PIL import Image, ImageTk
import serial.tools.list_ports

from utils.app_classes import *




class tk_gui():
    def __init__(self,master):
        self.root = master
        self.root.title("LinearTrack_er")
        
        self.display_resolution = [640*1.2, 360*1.2]
        self.is_streaming = False
        self.led_threshold = 50
        self.mask_colour = [0,0,255]
        self.session_running = False
        self.rest_running = False
        self.session_start = 0
        self.session_number = 1
        
        self.initialise_video()
        self.setup_gui()


    def initialise_video(self):
        
        self.get_avaliable_resolutions()
        low_res = self.avaliable_resolutions[-1]
        
        capture = cv2.VideoCapture(0,cv2.CAP_DSHOW)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, low_res[0])
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, low_res[1])
        ret, frame =  capture.read()
        
        #frame = cv2.flip(frame, 1)
        
        self.frame_resize_factor = [(low_res[0]/self.display_resolution[0]),(low_res[1]/self.display_resolution[1])]
        frame_resized = cv2.resize(frame, (int(frame.shape[1] / self.frame_resize_factor[1]),int(frame.shape[0] / self.frame_resize_factor[0]),),)
        
        #self.frame_resized = cv2.resize(frame_to_resize, (int(frame_to_resize.shape[1] / resize_factor[1]),int(frame_to_resize.shape[0] / resize_factor[0]),),)
        
        if ret:
            cv2image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGBA)
            last_frame = Image.fromarray(cv2image)
            self.tk_img = ImageTk.PhotoImage(image=last_frame)

        capture.release()

        self.viddims = frame_resized.shape[0:2]
    

    def setup_gui(self):
        """ Sets up the main GUI display with tkinter widgets
        """
    
        self.root.rowconfigure( (0,1), weight=1) 
        self.root.columnconfigure( (0,1), weight=1)  
        
        # create a frame at the top of the gui
        self.top_frame = ttk.Frame(self.root, height=self.viddims[0], width = 1000,style='Background.TFrame')
        self.top_frame.grid(row=0, column=0,sticky = 'nsew',padx=40, pady=(20,0))       
        self.top_frame.columnconfigure((0,1), weight=1)
        self.top_frame.rowconfigure((0,1,2,3), weight=1)
        
        self.video = video_pannel(self.top_frame,resolution = self.display_resolution,initial_img = self.tk_img)
        self.arduino = arduino_pannel(self.top_frame)
        self.set_logo(self.top_frame)


        # create a frame at the bottom of the gui
        self.bottom_frame = ttk.Frame(self.root, height = 500, width = 1000,style='Background.TFrame')
        self.bottom_frame.grid(row=1, column=0,sticky = 'nsew',padx=40, pady=(0,0))
        self.bottom_frame.columnconfigure((0,1), weight=1)
        self.bottom_frame.rowconfigure((0,1,2,3), weight=1)
        
        self.tracking = tracking_pannel(self.bottom_frame)
        self.aquisition = aquisition_pannel(self.bottom_frame, avaliable_resolutions = self.avaliable_resolutions_string)
        self.inscopix = inscopix_pannel(self.bottom_frame)
        self.experiment = experiment_pannel(self.bottom_frame)
        self.setup_theme_widget(self.bottom_frame)



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


    def set_logo(self,holding_frame):

        # set up the app logo and set the theme for the gui
        logo_img = Image.open("tktheme/theme/logos/trackerlogo.png")
        logo_img_small = logo_img.resize((220,40))
        self.logo_imgnew = ImageTk.PhotoImage(logo_img_small)
        
        logo_img_dark = Image.open("tktheme/theme/logos/trackerlogo_dark.png")
        logo_img_dark_small = logo_img_dark.resize((220,40))
        self.logo_imgnew_dark = ImageTk.PhotoImage(logo_img_dark_small)
        
        self.logo_canvas = tk.Canvas(holding_frame , width= 200, height= 0, highlightthickness=0,bg='#262626')
        self.logo_canvas.logo_img = self.logo_imgnew_dark
        self.logo_canvas.create_image(5,5,anchor=tk.SW, image=self.logo_imgnew_dark)
        self.logo_canvas.grid(row=0, column=1, sticky = 'sew', padx=(10),pady=(0,0),ipady=30)
        

    def setup_theme_widget(self, holding_frame):
        
        self.theme_frame = ttk.Frame(self.root)
        self.theme_frame.grid(
            row=3, 
            column=0,
            columnspan=3,
            padx=(0,0),
            pady=(10,0), 
            sticky = 'new'
            )
        self.theme_switch = ttk.Checkbutton(
            self.theme_frame, 
            style='Switch.TCheckbutton', 
            text="Light"
            )
        self.dark_label = tk.Label(self.theme_frame,text = 'Dark')
        #self.light_label = tk.Label(self.theme_frame,text = 'Light')
        
        
        self.theme_switch.pack(side='right',padx=(0,5), pady=2)
        self.dark_label.pack(side='right',padx=2, pady=2)
        self.root.iconbitmap("tktheme/theme/logos/tracker_icon.ico")



        
        
class video_pannel():
    def __init__(self, holding_frame, resolution, initial_img):
        self.holding_frame = holding_frame
        self.resolution = resolution
        self.image = initial_img
        self.setup_pannel()


    def setup_pannel(self):
        # setup the frame to house the webcam video feed and reward zone locations
        self.video_frame = ttk.Frame(self.holding_frame,style='Background.TFrame')
        self.video_frame.grid(row=0, column=0, rowspan=4, sticky='sew',pady=(0,10))
        
        self.video_canvas = tk.Canvas(self.video_frame, width=self.resolution[0], height=self.resolution[1],bd=0, highlightthickness=0, relief='ridge')
        self.video_canvas.image = self.image
        self.video_canvas.create_image(0,0, anchor=tk.NW, image=self.image, tag='video')
        self.video_canvas.tag_lower('video','all')
        self.video_canvas.grid(row=0, column=0)
        
        r1 = RewardZone(self.video_canvas, [145, 145, 205, 205], rewardport=1, name='Reward_Zone_1')
        r2 = RewardZone(self.video_canvas, [595, 145, 655, 205], rewardport=2, name='Reward_Zone_2')
        r3 = Rectangle(self.video_canvas,[206, 162, 594, 192], name='linear_track')
        self.crop_zone = CropZone(self.video_canvas,[85, 115, 695, 245], name='crop_zone')

        self.zones = [r1, r2, r3]


# LED Tracking settings pannel
class tracking_pannel():
    def __init__(self, holding_frame):
        self.holding_frame = holding_frame
        self.led_threshold = 50 
        self.setup_pannel()

    def setup_pannel(self):    
# Frame for tracking controls


        self.tracking_label = ttk.Label(
            self.holding_frame,
            text = "Tracking Controls",
            font=("Segoe Ui", 10),
            style='Background.TLabel'
            )
        self.tracking_label.grid(
            row=0, 
            column=0,  
            sticky="nw",
            ipady=6
            )
        
        self.tracking_frame = ttk.Frame(
            self.holding_frame, 
            height = 150, 
            width = 250,
            style = 'Card.TFrame'
            )
        self.tracking_frame.grid(
            row=1, 
            column=0, 
            columnspan=2, 
            pady=0,
            padx=(0,10), 
            sticky = 'nsew'
            )   
        self.tracking_frame.columnconfigure((0,1,2,3), weight=1)
        self.tracking_frame.rowconfigure((0,1,2,3), weight=1)
        
   
        
        


        # Overlay tracking position checkbox
        self.overlay_position = tk.IntVar(value=0)
        self.overlay_check = ttk.Checkbutton(
            self.tracking_frame, 
            variable=self.overlay_position, 
            text = 'Overlay Position'
            )
        self.overlay_check.grid(
            row=3, 
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
            row=3, 
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
            row=1, 
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
            row=1, 
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
            row=2, 
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
            row=2, 
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
            row=1, 
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
            row=1, 
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
            row=2, 
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
            row=2, 
            column=4, 
            sticky='w', 
            padx=(5,20),
            pady=5
            )
        
        # Track crop button - could change to a checkbox
        self.crop_button = ttk.Checkbutton(
            self.tracking_frame,
            text="Crop Track",
            width=10,
            style="Toggle.TButton"
            )
        self.crop_button.grid(
            row=3, 
            column=3, 
            columnspan=2, 
            padx=(5,20), 
            sticky='sew', 
            pady=(5,20)
            )




# Class for aquistion pannel
class aquisition_pannel():

    def __init__(self,holding_frame, avaliable_resolutions):
        self.holding_frame = holding_frame
        self.avaliable_resolutions = avaliable_resolutions
        self.setup_pannel()

    def setup_pannel(self):
        
        self.aqusition_label = ttk.Label(
            self.holding_frame,
            text = "Aquisition Controls",
            font=("Segoe Ui", 10),
            style='Background.TLabel'
            )
        self.aqusition_label.grid(
            row=2, 
            column=0,  
            sticky='sw',
            ipady=6
            )

        
        # Frame for aquisition controls
        self.aquisition_frame = ttk.Frame(
            self.holding_frame,
            style='Card.TFrame', 
            height = 140, 
            width = 150
            )
        self.aquisition_frame.grid(
            row=3, 
            column=0, 
            sticky = 'nsew', 
            pady=(0,5), 
            padx=(0,10)
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
            pady=(20, 10), 
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
            pady=(5,15), 
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
            pady=(5,15), 
            ipady=5,
            sticky='nsew'
            )

         

        # Frame to hold video resolution and FPS
        self.vid_res_frame = ttk.Frame(self.aquisition_frame)
        self.vid_res_frame.grid(
            row=2, 
            column=0, 
            columnspan=2,
            pady=(0,2),
            padx=(2,2)
            )
        #self.vid_res_frame.columnconfigure((0,1), weight=1) 
        
        # Video resolution selector spinbox
        self.video_res = tk.StringVar()
        self.vid_res_cb = ttk.Combobox(
            self.vid_res_frame,
            textvariable=self.video_res,
            height=4,
            width=20
            )
        self.vid_res_cb.grid(
            row=0, 
            column=1, 
            sticky='nsew', 
            pady=(0,5),
            padx=(2,5)
            )
        self.vid_res_cb['values'] = self.avaliable_resolutions
        self.vid_res_cb['state'] = 'readonly'
        self.vid_res_cb.set(self.avaliable_resolutions[-1])

        #self.set_camera_resolution()
        self.vid_res_cb.bind("<<ComboboxSelected>>",lambda e: self.holding_frame.focus())
        
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
            padx=2,
            )
                #custom button that is a shutter for cam settings
        self.cam_settings_button = ttk.Button(
            self.vid_res_frame,
            style='Logo.TButton'
            )
        self.cam_settings_button.grid(
            row=0, 
            column=2,  
            pady=2,
            sticky='nsew',
            padx=(5,10)
            )


class inscopix_pannel():
    def __init__(self, holding_frame):
        self.holding_frame = holding_frame
        self.setup_pannel()

    def setup_pannel(self):

        self.inscopix_label = ttk.Label(
            self.holding_frame,
            text = "Inscopix Controls",
            font=("Segoe Ui", 10),
            style='Background.TLabel'
            )
        self.inscopix_label.grid(
            row=2, 
            column=1,  
            sticky='sw',
            padx=(15),
            ipady=6
            )

        # Frame for Inscopix controls 
        self.inscopix_frame = ttk.Frame(
            self.holding_frame,
            style = 'Card.TFrame',
            width = 300
            )
        self.inscopix_frame.grid(
            row=3, 
            column=1, 
            sticky = 'nsew', 
            pady=(0,5), 
            padx=(15,10)
            )
        
        # Activate Opto Zone tracking position checkbox
        self.activate_opto = tk.IntVar(value=0)
        self.activate_opto_check = ttk.Checkbutton(
            self.inscopix_frame, 
            variable=self.activate_opto, 
            text = 'Activate Optogenetic Zone'
            )
        self.activate_opto_check.grid(
            row=0, 
            column=0,
            columnspan=2, 
            sticky='nsew',
            pady=(20,5),
            padx=(20,10),
            )
        
        # Opto Zone correction mode
        self.opto_correct = tk.IntVar(value=1)
        self.opto_correct_check = ttk.Checkbutton(
            self.inscopix_frame, 
            variable=self.opto_correct, 
            text = 'OptoZone Correction',
            state='disabled'
            )
        self.opto_correct_check.grid(
            row=1, 
            column=0,  
            columnspan=2,
            sticky='nsew', 
            padx=(20,20),
            pady=(5,10)
            )
        
        self.optoseperator = ttk.Separator(self.inscopix_frame)
        self.optoseperator.grid(
            row=2, 
            column=0,
            columnspan=2,  
            padx=(40), 
            pady=(0),
            sticky='nsew'
            )

        # Opto on Button 
        self.opto_on = tk.IntVar(value=0)
        self.opto_on_button = ttk.Checkbutton(
            self.inscopix_frame, 
            text="Opto On", 
            style="Toggle.TButton", 
            variable=self.opto_on
            )
        self.opto_on_button.grid(
            row=3, 
            column=0, 
            padx=(20, 10), 
            pady=(15, 10), 
            ipady= 5,  
            sticky='nsew'
            )
        
        # Opto on Button
        self.opto_off_button = ttk.Button(
            self.inscopix_frame, 
            text="Opto Off", 
            style="Toggle.TButton"
            )
        self.opto_off_button.grid(
            row=3, 
            column=1, 
            padx=(10, 20), 
            pady=(15, 10),
            ipady= 5,  
            sticky='nsew'
            )
        


class experiment_pannel():
    def __init__(self, holding_frame):
        self.holding_frame = holding_frame
        self.session_number = 1
        self.setup_pannel()
        

    def setup_pannel(self):
        
        

        self.experiment_label = ttk.Label(
            self.holding_frame,
            text = "Experiment Controls",
            font=("Segoe Ui", 10),
            style='Background.TLabel'
            )
        self.experiment_label.grid(
            row=0, 
            column=2,  
            sticky='nw',
            padx=(15,5),
            ipady=6
            )
        
        self.experiment_frame = ttk.Frame(self.holding_frame, style='Card.TFrame', width = 330)
        self.experiment_frame.grid(row=1, column=2, rowspan=3, pady=(0,5), padx=(15,0), sticky = 'nsew')

        self.experiment_frame.columnconfigure((0,1), weight=1)
        self.experiment_frame.rowconfigure((0,1,2,3), weight=1)
        
        
        # start session button
        self.session_but_state = tk.IntVar(value=0)
        self.start_session_button = ttk.Checkbutton(
            self.experiment_frame, 
            text="Start Session", 
            style="Toggle.TButton", 
            variable=self.session_but_state
            )
        self.start_session_button.grid(
            row=0, 
            column=0, 
            padx=(50, 50), 
            pady=(30, 10),  
            sticky='nsew'
            )
        
        #start rest button
        self.rest_but_state = tk.IntVar(value=0)
        self.start_rest_button = ttk.Checkbutton(
            self.experiment_frame,
            text="Start rest", 
            style="Toggle.TButton",
            variable=self.rest_but_state
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
            pady=(20,10), 
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

        
        self.vcmd = (self.experiment_frame.register(self.onValidate))

        # Session length text and value
        self.session_length_label = tk.Label(
            self.length_frame,
            text = "Session Length:"
            )
        self.session_len = tk.IntVar(self.length_frame,10)
        self.session_length_input = ttk.Entry(
            self.length_frame,
            textvariable= self.session_len, 
            width = 5,
            validate="key",
            validatecommand = (self.vcmd, '%P')
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
            width = 5,
            validate="key",
            validatecommand = (self.vcmd, '%P')
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
        self.auto_session = tk.IntVar(value=1)
        self.auto_session_len = ttk.Checkbutton(
            self.length_frame, 
            variable=self.auto_session, 
            text = 'Auto session length'
            )
        self.auto_session_len.grid(
            row=2, 
            column=0,
            columnspan=2, 
            ipady=5, 
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
        self.save_dir = tk.StringVar(self.saving_frame ,"C:/temp")
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
            ipady = 4, 
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
            ipady= 5, 
            sticky='nsew'
            )
        
        # Frame for reset buttons
        self.reset_button_frame = tk.Frame(self.experiment_frame)
        self.reset_button_frame.grid(
            column = 1, 
            row = 3, 
            pady=(0,2),
            padx=(0,2), 
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
    def onValidate(self, P):
        
        if str.isdigit(P) or P == "":
            if len(P)>0 and P[0] == "0":
                return False
            else:
                return True
        else:
            return False
        

class arduino_pannel():
    def __init__(self, holding_frame):
        self.holding_frame = holding_frame
        self.get_com_ports()
        self.setup_pannel()

    def setup_pannel(self):
        
        self.arduino_label = ttk.Label(
            self.holding_frame,
            text = "Arduino Controls",
            font=("Segoe Ui", 10),
            style='Background.TLabel'
            )
        self.arduino_label.grid(
            row=1, 
            column=1,  
            sticky='nw',
            padx=(10,5),
            pady=(0,0),
            ipady=6
            ) 
        
        
        self.arduino_frame = ttk.Frame(
            self.holding_frame, 
            style='Card.TFrame'
            )
        
        self.arduino_frame.grid(
            row=2, 
            column=1,
            rowspan=2, 
            padx=(10,0),
            pady=(5,10), 
            sticky = 'sew'
            )
        
        self.arduino_frame.columnconfigure((0,1,2), weight=1)
        self.arduino_frame.rowconfigure((0,1,2,3,4), weight=1)

        # Frame to house session infomration
        self.connection_frame = ttk.Frame(
            self.arduino_frame,
            style='Card.TFrame'
            )
        self.connection_frame.grid(
            row=0, 
            column=0, 
            columnspan=3, 
            sticky = 'n', 
            pady=(20,20), 
            padx=(10,10)
            )
        self.connection_frame.columnconfigure((0,1), weight=1)
        self.connection_frame.rowconfigure((0,1,2,3,4), weight=1)


        #session number text and value
        self.arduino_label = tk.Label(
            self.connection_frame,
            text = ("Arduino Connection"),
            font=("Segoe Ui", 12)
            )
        self.arduino_label.grid(
            row=0, 
            column=0,
            columnspan=2, 
            pady=5, 
            padx=10
            )

        self.comport_selected = tk.StringVar()
        self.serial_port_cb = ttk.Combobox(
            self.connection_frame,
            textvariable=self.comport_selected,
            width=10
            )
        self.serial_port_cb.grid(
            row=1, 
            column=0,
            columnspan=2, 
            pady=5, 
            padx=10
            )
        
        self.serial_port_cb['values'] = self.comports_avaliable
        self.serial_port_cb['state'] = 'readonly'
        self.serial_port_cb.set(self.comports_avaliable[0])

                #session number text and value
        self.arduino_connect_label = tk.Label(
            self.connection_frame,
            text = ("Select Arduino COM port"),
            font=("Segoe Ui", 10)
            )
        self.arduino_connect_label.grid(
            row=2, 
            column=0,
            columnspan=2,  
            padx=10
            )
                # Reset session button
        self.arduino_connect_button = ttk.Button(
            self.connection_frame,
            text="Connect" 
            )
        self.arduino_connect_button.grid(
            row=3, 
            column=0,  
            padx=(10, 5), 
            pady=(5, 10),
            )
        
        # Reset rest button
        self.arduino_disconnect_button = ttk.Button(
            self.connection_frame,
            text="Disconnect",
            state="disabled"
            )
        self.arduino_disconnect_button.grid(
            row=3, 
            column=1,  
            padx=(5, 10), 
            pady=(5, 10),
            )

        self.solnoid_1_label = tk.Label(
            self.arduino_frame,
            text = ("Reward Port 1"),
            font=("Segoe Ui", 12)
            )
        self.solnoid_1_label.grid(
            row=2, 
            column=0,  
            padx=(10,0)
            )
        self.solnoid_2_label = tk.Label(
            self.arduino_frame,
            text = ("Reward Port 2"),
            font=("Segoe Ui", 12)
            )
        self.solnoid_2_label.grid(
            row=2, 
            column=2,  
            padx=(0,10)
            )

        self.seperator = ttk.Separator(self.arduino_frame, orient='vertical')
        self.seperator.grid(
            row=3, 
            column=1,
            rowspan=3,  
            padx=(0), 
            pady=(0),
            sticky='ns'
            )
        
        self.solinoid_switch_1_val = tk.IntVar(value=0)
        self.solinoid_1_switch = ttk.Checkbutton(
            self.arduino_frame, 
            style='Switch.TCheckbutton',
            variable=self.solinoid_switch_1_val
            )
        self.solinoid_1_switch.grid(
            row=4,
            column=0,
            padx=(5,0), 
            ipady=5
            )
        
        self.solinoid_1_state_label = tk.Label(
            self.arduino_frame, 
            text="Closed"
            )
        self.solinoid_1_state_label.grid(
            row=3,
            column=0,
            padx=0, 
            pady=0,
            sticky='n'
            )
        
        self.solinoid_switch_2_val = tk.IntVar(value=0)
        self.solinoid_2_switch = ttk.Checkbutton(
            self.arduino_frame, 
            style='Switch.TCheckbutton',
            variable=self.solinoid_switch_2_val
            )
        self.solinoid_2_switch.grid(
            row=4,
            column=2,
            padx=(5,0), 
            ipady=5
            )
        
        self.solinoid_2_state_label = tk.Label(
            self.arduino_frame,
            text = 'Closed'
            )
        self.solinoid_2_state_label.grid(
            row=3,
            column=2,
            padx=0, 
            pady=0,
            sticky='n'
            )
        
        self.solinoid_1_button = ttk.Button(
            self.arduino_frame,
            text="Trigger\nReward 1" 
            )
        self.solinoid_1_button .grid(
            row=5, 
            column=0,  
            padx=(10, 0), 
            pady=(5, 10),
            )
        
        self.solinoid_2_button = ttk.Button(
            self.arduino_frame,
            text="Trigger\nReward 2" 
            )
        self.solinoid_2_button.grid(
            row=5, 
            column=2,  
            padx=(0, 10), 
            pady=(5, 10),
            )
        
        self.solinoid_switch_3_val = tk.IntVar(value=1)
        self.solinoid_3_switch = ttk.Checkbutton(
            self.arduino_frame, 
            style='Switch.TCheckbutton',
            variable=self.solinoid_switch_3_val
            )
        self.solinoid_3_switch.grid(
            row=7,
            column=2,
            padx=(10,2),
            sticky='w',
            pady=(10,5), 
            ipady=5
            )
        self.solinoid_3_state_label = tk.Label(
            self.arduino_frame,
            text = 'Open'
            )
        self.solinoid_3_state_label.grid(
            row=7,
            column=2,
            padx=(0,10), 
            pady=0,
            sticky='e'
            )
        # Probabilistic reward checkbox
        self.probability_reward = tk.IntVar(value=0)
        self.probility_reward_check = ttk.Checkbutton(
            self.arduino_frame, 
            variable=self.probability_reward, 
            text = 'Probabilistic reward'
            )
        self.probility_reward_check.grid(
            row=7, 
            column=0,
            columnspan=2, 
            pady=5,
            padx=(5,0), 
            sticky='w',
            )
        

    def get_com_ports(self):
        
        self.comports = serial.tools.list_ports.comports()

        self.comport_described = []
        self.comports_avaliable = []
        for port in sorted(self.comports):
            display_string = (str(port.name) + ": " + str(port.description[:-7]))
            self.comport_described.append(display_string)    
            self.comports_avaliable.append(str(port.name))
            #print(display_string)
