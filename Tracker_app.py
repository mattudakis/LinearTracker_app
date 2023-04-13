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

from utils.tk_gui_class import tk_gui



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
        self.reward_zones = app.gui.video.zones #get location of reward zones
        pos = self.tracked_position
        
        inzone = np.zeros(3,dtype=int)
        for i, zone in enumerate(self.reward_zones):
           inzone[i] = zone.is_occupied(pos)
           
        if any(inzone):
            zone_occupied = np.argwhere(inzone)
            zone_occupied = np.concatenate(zone_occupied,axis=None)
            zone_occupied = min(zone_occupied) #if there are multi zones occupied take the lowest one
            
            print(f"Zone {zone_occupied} occupied")
      
    
""" 

TRACKER CLASS


"""

class tracker_app():
    def __init__(self,master):
        self.root = master
        self.root.protocol("WM_DELETE_WINDOW", self.closeWindow)


        self.is_streaming = False
        self.led_threshold = 50
        self.mask_colour = [0,0,255]
        self.session_running = False
        self.rest_running = False
        self.session_start = 0
        self.session_number = 1
        
        self.possition_array = np.zeros((50,2),dtype=int)
        
        self.gui = tk_gui(self.root)
        self.cam = video_stream() # create a video stream instance 
        self.set_camera_resolution()
        self.bind_callbacks()
       
    def bind_callbacks(self):
        self.gui.experiment.start_session_button.configure(command= self.start_stop_session_button) 
        self.gui.experiment.start_rest_button.configure(command= self.start_stop_rest_button) 
        self.gui.experiment.save_dir_button.configure(command= self.get_save_dir)
        self.gui.experiment.reset_sessions_button.configure(command= self.reset_sessions)
        self.gui.experiment.reset_experiment_button.configure(command= self.reset_sessions)
        
        self.gui.tracking.thresh_slider.configure(command=self.update_led_thresh) 
        self.gui.tracking.ledsize_slider.configure(command=self.update_ledsize)
        self.gui.tracking.led_colour_spin.configure(command=self.Led_to_track)
        self.gui.tracking.crop_button.configure(command=self.crop_track)

        self.gui.aquisition.stream_button.configure(command=self.start_stop_stream_button)
        self.gui.aquisition.start_button.configure(command= self.start_rec_button)
        self.gui.aquisition.stop_button.configure(command= self.stop_rec_button)
        self.gui.aquisition.vid_res_cb.bind('<<ComboboxSelected>>', self.set_camera_resolution)
        
        self.gui.theme_switch.configure(command= self.change_theme)


    def Led_to_track(self):
        led_colour = self.gui.tracking.colour_to_track.get()
        self.gui.tracking.ledsize_label['text'] = (led_colour + " Size")
        self.gui.tracking.thresh_label['text'] = (led_colour + " Threshold")
        
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
            self.gui.logo_canvas.delete('all')
            self.gui.logo_canvas.logo_img = self.gui.logo_imgnew
            self.gui.logo_canvas.create_image(5,5,anchor=tk.NW, image=self.gui.logo_imgnew)
        else:
            # Set dark theme
            self.root.tk.call("set_theme", "dark")
            self.gui.logo_canvas.delete('all')
            self.gui.logo_canvas.logo_img = self.gui.logo_imgnew_dark
            self.gui.logo_canvas.create_image(5,5,anchor=tk.NW, image=self.gui.logo_imgnew_dark)


    def update_led_thresh(self,val):
        self.led_threshold = int(self.gui.tracking.thresh_slider.get())
        self.cam.led_thresh = self.led_threshold
    

    def update_ledsize(self,val):
        self.ledSize = int(self.gui.tracking.ledsize_slider.get())
    

    def crop_track(self):
        print("cropping Track yet to be implemented")


    def get_save_dir(self):
        save_directory = filedialog.askdirectory()
        self.gui.experiment.save_dir.set(save_directory)
        

    def reset_sessions(self):
        self.session_number = 1
         
    
    def set_camera_resolution(self,*args):
        """ Sets video camera video resolution and 
            calculates resize factor for display frame  
        """        
        vid_res_index = self.gui.aquisition.vid_res_cb.current()
        camera_resolution = self.gui.avaliable_resolutions[vid_res_index]
        
        self.cam.video_resolution = camera_resolution
        self.frame_resize_factor = [
                                   (camera_resolution[0]/self.gui.display_resolution[0]),
                                   (camera_resolution[1]/self.gui.display_resolution[1])
                                   ]
        
        
    def start_stop_session_button(self):
        """ Start/stop session timmer button 
        """
        if self.session_running: 
            print("stoping_session")
            self.gui.experiment.start_session_button.config(text="Start Session")
            self.session_running = False
            self.session_number += 1
        else:
            self.session_start = datetime.now()
            print("starting session")
            self.gui.experiment.start_session_button.config(text="Stop Session")
            self.session_running = True
         
    
    def start_stop_rest_button(self):
        """ Start/stop rest timmer button 
        """
        if self.rest_running: 
            print("stoping rest")
            self.gui.experiment.start_rest_button.config(text="Start Rest")
            self.rest_running = False
        else:
            self.rest_start = datetime.now()
            print("starting rest")
            self.gui.experiment.start_rest_button.config(text="Stop Rest")
            self.rest_running = True
    
    
    def start_stop_stream_button(self):
        """ Start/stop video stream button 
        """
        if self.cam.running:
            # Stop the video stream
            self.is_streaming = self.cam.stop_stream()
            
            # Update GUI buttons
            self.gui.aquisition.stream_button.configure(text="Start Stream")
            self.gui.aquisition.stream_button.configure(state="normal")
            self.gui.aquisition.rec_but_state.set(0)
            self.gui.aquisition.start_button.configure(text="Record")
            self.gui.aquisition.start_button.configure(state="normal")
            self.gui.aquisition.stop_button.configure(state="disabled")
            self.gui.aquisition.vid_res_cb.configure(state="readonly")
            
            return
        else:    
            # Start the video stream
            self.is_streaming = self.cam.start_stream()
            self.gui.aquisition.stream_button.configure(text="Streaming... Press to stop")
            self.gui.aquisition.vid_res_cb.configure(state="disabled")

        # if app is streaming, start display update loops
        if self.is_streaming:
            self.update_frame()
            self.refresher()
                
    
    def start_rec_button(self):         
        # start the video stream recording
        time_now = datetime.now()
        vid_time_stamp = time_now.strftime("%Y%m%d_%H%M%S")
        ID_stamp = self.gui.experiment.animal_id.get()
        session_stamp = str(self.session_number)
        vidname = (ID_stamp + "_Session_" + session_stamp + "_" + vid_time_stamp)
        print("recording video: " + vidname)
        self.cam.vid_tag = vidname
        self.cam.start_record()
        
        # update the GUI buttons
        self.gui.aquisition.start_button.configure(text="Recording...")
        self.gui.aquisition.start_button.configure(state="disabled")
        self.gui.aquisition.stream_but_state.set(1)
        self.gui.aquisition.stream_button.configure(text="Streaming... Press to stop")
        self.gui.aquisition.stop_button.configure(state="normal")
        self.gui.aquisition.vid_res_cb.configure(state="disabled")
        
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

        self.gui.aquisition.start_button.configure(text="Record")
        self.gui.aquisition.rec_but_state.set(0)
        self.gui.aquisition.start_button.configure(state="normal") 
        self.gui.aquisition.stop_button.configure(state="disabled")
    

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
                
            self.gui.experiment.session_time_label_val['text'] = session_time_string
            self.gui.experiment.session_number_label_val['text'] = (str(self.session_number))
        

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
            
            self.gui.experiment.rest_time_label_val['text'] = rest_time_string   
        
        
    def refresher(self):
        self.gui.aquisition.fps_string_var.set(f'FPS: {self.cam.fps:.2f}')
        
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
            if self.gui.tracking.overlay_position.get():
                possition_data = self.get_tracked_data()
                for pos in possition_data:
                    center = (pos[0],pos[1])
                    radius = 4
                    width = 1
                    self.frame = cv2.circle(self.frame, center, radius, (0, 0, 255), width)
                
            if self.gui.tracking.frame_to_display.get() == 'LED Mask': 
                self.frame[self.cam.final_mask==255] = self.mask_colour
            
            cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
            self.last_frame = Image.fromarray(cv2image)
            tk_img = ImageTk.PhotoImage(image=self.last_frame)
            
            self.gui.video.video_canvas.tk_img = tk_img
            self.gui.video.video_canvas.create_image(0,0, anchor=tk.NW, image=tk_img, tag='video')
            self.gui.video.video_canvas.tag_lower('video','all')
            
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

    
    
