# blenderSubprocessRender
Render a blender animation in multiple threads using subprocess

## The Problem
Blender natively does multithreaded rendering on a single frame. This is not 
optimal for render a video. Each video frame is usually a single image and does
not require much to render. 

## The Solution
Break up the scene's start and end frames into sub-sections and run multiple 
instances of Blender simultaneously. This allows parallel rendering of frames.

## Usage
First off, you will need to set Blender to output individual frames. I find 
`JPEG` at 80% quality is a good setting. You need to set your output path to 
contain the frame numbers as well, I use `//frames/output_######.jpg`.

When the addon is installed you will have a new panel in the render options. At
the top you will have three choices:

 - **All**: Use all threads for rendering
 - **Only**: Use only the specified number of threads
 - **Except**: Use the number of all threads minus the specified number

You will then set a new output for the combined frames to be joined into. 

You can change the settings that are used with FFmpeg if you need to customize
the output. If you need to reset back to the default settings, right click the 
text box and select the reset option from the popup. 

## Setup
You will need to install ffmpy with pip so blender can use FFMpeg. Blender is
uses Python 3 for plugins so you will need to specify that when installing.

 1. Install [FFMPEG](https://www.ffmpeg.org/) on your system
 2. Download [get-pip.py](https://bootstrap.pypa.io/get-pip.py)
 3. Run `get-pip.py` with the version of python blender is using. Likely
	`sudo python3 ./get-pip.py`
 4. Use that pip install to install `ffmpy`. Likely `sudo pip3 install ffmpy`

\*Note: Only tested on Ubuntu

