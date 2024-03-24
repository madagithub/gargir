# I'm a Bean

## General
This exhibit shows a wheat growing footage, while taking input from a camera, fixed at designated holes in which you can put your head in.
When people put their heads in the hole, the live camera feed recognizes it has a face on it, and inorporates their face throughout the wheet growing video.
Each face spot has its own designated and pre-planned places in the footage in which it is incorporated, using transparancy to have a good integration effect.

The exhibit supports three modes:
Running mode, which is as described.
Edit mode, which allows to edit the places where each face will be incorporated in the video. This is done by defining key frames, and is detailed bellow.
Calibrate mode, which allows setting up the camera properly so that the faces will be extracted correctly. How to calibrate is described in detail below as well.

This entire exhibit can theoretically be used to define and incorporate faces in any video, by defining key frames and calibrating the camera properly.

## Installation & Run
The exhibit runs using python 3 on linux, using the opencv library (known as cv2), and pygame (to play the video sound) as well as dlib for face recognition.
The exhibit is designed for a screen of 1920x1080 resolution, with two webcams connected.

After the latest python 3 installation, use:

```
pip3 install numpy
pip3 install opencv-python
pip3 install dlib
pip3 install pygame
```

To install all necessary packages.

Then, to run, go to the root project dir and run:

```
python3 iamabean.py MODE
```

With MODE being either run, test, edit or camera (for calibration).
run is the default action if none specified and runs the exhibit.
test uses a fixed image as a dummy input instead of a live camera, for testing purposes with no live camera available.
edit runs the editor, to fix or update face embedding positions in the video.
Finally, camera is the calibration mode used to setup the camera correctly.

## Log
This exhibit has no log implemented.


## Configuration File
The configuration file named iamabean.json holds all the info needed for key frames defined by the editor.
A key frame defines the position of one of the faces coming from the camera in a certain frame of the video.
Each key frame defines a rectangle, under which the face will be bound to and embedded in that position.

The rectangle is defind by x/y of the top left corner and the width/height of it, in pixels, matching the screen size (which matches the video size).
In addition, a rotation (around its center), defined by radians, is saved as well for each rectangle.

Finally, the mask opacity value to use is saved.
There are masks going from 0.5 opacity up to 0.95 opacitiy, in jumps of 0.05 (see Mask Creation section below on how they were created if there is a need to updated them). Each key frame also chooses which mask to use, with higher opacity taking more face and less background, and the lowest one tkaing exactly half of the face and half of the background (the 0.5 opacity).

Between key frames, linear interpolation is used. This can save defining exact rectangles for each frame, which can be tedious.
Instead, you can define a key frame for frame 1, and a key frame for frame 30, and if there is a movement that is linear between those frames, the end result should suffice.
However, in some places in the video, where you want the face to jump about (like the beans spilling at the end of the video), you would want to set a different key frame per frame to have the exact behaviour.

Sometimes, it is necessary to not show a face for a few frames, or show one of the faces only.
To do that, you can set a key frame for out of screen, right after an in-screen key frame.

The configuration file structure is simply a json array with each object in the array specifying a key frame.
Each key frame contains a rectIndex key specifying 0 for the first face or 1 for the second face (as a key frame doesn't have to contain both faces, one can be linearly interpolated at that time). Also, the vidoe frame is specified in the key keyFrameIndex, which is zero-based.
Finally, the position key holds the x/y/rotation properties and the size key holds the width/height key of the rectnagle.
The mask key holds the opacity of the mask chosen.

x and y values goes positive from left to right, and top to bottom respectively.

Here's a sample key frame object:

```
{
	"rectIndex": 0,
	"keyFrameIndex": 48,
	"position": 
	{
		"x": 333, 
		"y": 435, 
		"rotation": -6.938893903907228e-18
	}, 
	"size": 
	{
		"width": 78,
		"height": 152
	},
	"mask": "0.85"
}
```

Note that, if you do not want a face to be shown, you can put a position that's outside of screen (for example, high and negative).
However, note that it will the interpolate from last key frame. So the frame before must be a key frame with a position to prevent that.
Also, note that if you want to eliminate a face for a length of a few frames, you can use two outside of screen frames at start and end of range, then the interpolation between them will keep them out of screen. Then, the next frame after the last out of screen one should be a key frame giving the next location.

## Editor
The editor is used to load and update the configuration file easily. It can also be used to create a completely new configuration file for a different video, theoretically.

The editor is controlled mostly via keyboard, but with the mouse as well.
All actions can be done with the keyboard, the mouse makes some shortcuts.

It allows navigating through the frames and key frames of the video, and defining (or updating/deleting) key frames.

The editor loads automatically on startup the definitions from imabean.json, and allows saving to it (overwriting) after updates.

Following are the keys used in the editor and their actions:

### Navigation

Note that at all times, the editor holds the current video frame viewed, initialized to 0.
These keys allow navigating through video frames and key frames.

**'i'**: Go to next video frame.
**'u'**: Go to prev video frame.
**'m'**: Go to next key frame (if exists).
**'n'**: Go to prev key frame (if exists).

**'p'**: Change to play mode, so vidoe starts playing (then you can use 's' to change back to edittor). Useful for moving large chunk of video quickly.

### Key Frames Editting

**'K'**: Create a key frame on current video frame (if it does not exist).

**'M'**: Create a key frame on current video frame and make its data the same as the next key frame defined. Useful to get same position easily.

**'N'**: Create a key frame on current video frame and make its data the same as the previuos key frame defined. Useful to get same position easily.

**'d'**: Delete current key frame (if you are on one).


**'c'**: Change the face you are working on.

**'x'**: Add one to current rectangle's x.

**'X'**: Subtract one from current rectangle's x.

**'y'**: Add one to current rectangle's y.

**'Y'**: Subtract one from current rectangle's y.

**'w'**: Add one to current rectangle's width.

**'W'**: Subtract one from current rectangle's width.

**'h'**: Add one to current rectangle's height.

**'H'**: Subtract one from current rectangle's height.

**'r'**: Add one degree to current rectangle's rotation.

**'R'**: Subtract one degree from current rectangle's rotation.

**'a'**: Add 0.5 to current mask's opacity.

**'A'**: Subtract 0.5 from current mask's opacity.

**'E'**: Moves rectangle position to out of screen (to eliminate face from current frame, putting it in -1000/-1000).

**'e'**: Moves rectangle position to center of screen (used mostly to remove from out of screen position).

**'S'**: Overwrite imabean.json configuration file with all changes up to now.

Note that you can see a key frame exists for a certain rectangle if its order is light red or light blue, and not dark red or dark blue.
Also, if a key frame exists, you'll see on the top left corner of the screen a circle marking the current face chosen (that you can change with 'c') and the transparancy of the mask currently chosen.

### Using the Mouse

The mouse can help shortcut some of the navigation issues.
You can drag the current frame rectnagle (show at the bottom of the screen) left and right to jump to a far away frame instantly.
You can also drag on the screen itself to both draw a rectangle from scratch, or drag an existing rectangle.
This helps updating the rectangle positions easily.

## Calibration

It may be an issue where the camera needs to be replaced.
To have it easily placed at the correct place, it is possible to run the script in calibration mode with the parmaeter camera.
It will then get the live camera output, show it, and draw the rectangles boudning the faces on it.
If, the rectangles don't match the holes used for the faces, you can adjust the camera so it fits, and then fix it to the wall again.
This is helpful for anytime the camera needs to be re-placed, after moving the exhibit etc.

To run calibration mode use this command:

```
python3 iamabean.py camera
```

## Test Mode

A specific camera fake input featuring Dima's faces twice exists in camera-stream.jpg.
If you run the script with test as the only parameter, no live camera needs to be connected, but the stream will be taken from that picutre.
Use it to test the positions of the faces after updating them with the editor easily, with no need for a live camera connected and a specitic layout.

Test mode should be run like this:

```
python3 iamabean.py test
```

## Matching Audio and Video

A specific issue with this exhibit is to match the audio and the video.
The audio is played using pygame, but the rate of the video maybe a bit slower, as processing time is needed to adjust the faces from live camera.

To solve this issue, the game times the amount of time passed from the beginning of the live camera processings, and then waits the additional frame time.
Frame time is assumed to be 30 miliseconds, but that may change in other videos, or based on specific computer or video parameters.
So, if necessary, you should adjust the code and update the 28 number with an appropriate one, based on the number of miliseconds each frame should take.

You will find this in line 673 of the imabean.py script:

```
waitTime = 30 - time
```

In the last exhibit, due to the processing time taking too long, 28 was used instead of 30 to have the sound match the video.

## Mask Creation Scripts

The script contains a shell script that uses imageMagick and creates all the masks needed.
Note that in any future development where different masks are needed, you should update this script.

To run ths script, first install imagemagick on linux, following instructions here:
https://imagemagick.org/script/download.php

Then run it from root directory:

```
./create-masks.sh
```

It then creates masks named first-mask-ellipse-X.png and second-maskellipse-X.png with X ranging from 0.5 to 0.95 in jumpst of 0.05.
