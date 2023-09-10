![Trackerlogo](media/trackerlogo_dark1.png#gh-dark-mode-only)
![Trackerlogo](media/trackerlogo1.png#gh-light-mode-only)


**Desktop app for real-time tracking and experimental control - developed using Python, OpenCV and tkinter**

>
> :small_blue_diamond: Record and track the position of a rodent via detection of rodent-mounted LED.
> 
> :small_blue_diamond: Reward delivery and optogenetic stimulation can be triggered when the rodent enters ROI zones.
> 
> :small_blue_diamond: Serial connection to an Arduino can trigger hardware, such as optogenetic lasers/reward valves.
>

&nbsp;


## Features
- Real-time LED (r,g,b) tracking. 
- Stream/record webcam video.
- Adjustable parameters sliders for optimised LED detection.
- Video overlays for the tracked position/ LED colour mask.
- Adjustable ROIs to define tracking zones.
- Serial connection to an Arduino to trigger hardware.
- Output CSV data, such as video timestamps, tracked coordinates and experiment logic.
- Experiment metrics/controls, such as lap count, session time and automatic session durations.

&nbsp;


## User interface
![App screen](media/screenshot.png) ![App screen](media/screenshot_light.png)

&nbsp;

## Personal use case

### `Experiment`

We wanted to record the Ca2+ activity of hippocampal neurons using miniaturised microscopy whilst mice explored a linear track, to study the spatial encoding of hippocampal place cells. We then aimed to perturb specific cell types with optogenetics at specific locations of the track during the behaviour.

To do this we needed real-time low latency position tracking of the mouse, video recording and accurate automated location-based triggering of reward delivery and optogenetic stimulation. 

&nbsp;

### `Motivation for development` 

Commercial software and hardware could achieve this goal but require significant investment. Opensource deep learning solutions such as DeepLabCut require advanced computer hardware, do not generalise well and are computationally too expensive for our relatively straightforward use case. 

I sought to develop a open-source desktop application that could take advantage of simple tracking of head-mounted LEDs which are often used in similar behaviour experiments in neuroscience. Developed in Python using standard webcam cameras and non-specialist computer hardware this software should generalise to other labs.

Personally, this project also allowed me to develop my Python programming skills, particularly object-orientated programming and using a model view controller architecture. 

&nbsp;

### `Implementation`

**Front end GUI**

- The GUI was designed using tkinter with custom themes (to make it look pretty).
- An all-in-one GUI window allowed for all experiment controls to be easily accessible.
- Light and dark themes were added for accessibility.

**Backend model**

- Video capture and LED tracking are run in a dedicated thread using Python’s threading module and openCV.
- LED tracking implemented via colour thresholding with users adjustable model parameters via the GUI.
- Video capture at multiple resolutions uses ffmpeg encoding and video output in .avi format.
- Tracking data is exportable as CSV files containing multiple tracking parameters and video timestamps.
- Arduino communication is achieved via USB comport connectivity.

&nbsp; 

### `Outcome` 

The LED tracking approach is fast and efficient allowing near-realtime position tracking at 30fps. Regions of interest can be drawn on the track which via a serial connection to an Arduino can trigger both reward delivery and TTL pulses to trigger optogenetic stimulation. This was successfully used for the study leading to interesting scientific output. 

&nbsp;

### `Future direction`

- A Kalman filter could be used to predict future positions, this would provide closer to real-time position tracking.
- If animal-mounted LEDs aren't available,  alternative models could be implemented, such as a deep lab cut model or other computer vision approaches.
> Thresholding of the rodent against a contrasting coloured maze could be used. In our case we had a black rodent on a black maze making this difficult.
- Ability to set custom maze rules.
- Adding .config compatibility to have custom default settings.




 
