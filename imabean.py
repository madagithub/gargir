import numpy as np
import cv2
import random
import sys
import json

RUN_MODE = 'run'
EDIT_MODE = 'edit'

NONE = 0
DRAGGING_FRAME = 1
DRAWING_RECT = 2
MOVING_RECT = 3

#SINGLE_FRAME = 0
#LINEAR_MOVEMENT = 1

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

SCROLLER_MARGIN = 10
SCROLLER_HEIGHT = 60
SCROLLER_WIDTH = 20
FRAME_SCROLLER_Y = SCREEN_HEIGHT - SCROLLER_HEIGHT - SCROLLER_MARGIN
SCROLLER_START_X = SCROLLER_MARGIN
SCROLLER_END_X = SCREEN_WIDTH - SCROLLER_MARGIN - SCROLLER_WIDTH

FIRST_RECT_INDEX = 0
SECOND_RECT_INDEX = 1

def drawFaceRect(frame, rectKeyFrame, color, face):
    global cameraImage

    start = (int(rectKeyFrame['position']['x']), int(rectKeyFrame['position']['y']))
    end = (int(rectKeyFrame['position']['x'] + rectKeyFrame['size']['width']), int(rectKeyFrame['position']['y'] + rectKeyFrame['size']['height']))

    cv2.rectangle(frame, start, end, color ,3)

    # Draw crop from camera
    if (face is not None):
        face = cv2.resize(face, (int(rectKeyFrame['size']['width']), int(rectKeyFrame['size']['height'])), interpolation = cv2.INTER_AREA)
        rows, cols = face.shape[:2]
        frame[int(rectKeyFrame['position']['y']):int(rectKeyFrame['position']['y'])+rows, int(rectKeyFrame['position']['x']):int(rectKeyFrame['position']['x'])+cols] = face
        #M = np.float32([[1,0,rectKeyFrame['position']['x']],[0,1,rectKeyFrame['position']['y']]])
        #face = cv2.warpAffine(face, M, (cols, rows))

    #text = 'Single' if rectKeyFrame['transition'] == SINGLE_FRAME else 'Linear'
    #y = 150 if rectKeyFrame['rectIndex'] == 1 else 180
    #cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

def interpolateValues(first, second, ratio):
    return (first + (second - first) * ratio)

def interpolateRects(firstRect, firstFrame, secondRect, secondFrame, currFrame):
    framesDiff = secondFrame - firstFrame
    ratio = float(currFrame - firstFrame) / framesDiff;
    return {
        'position': {
            'x': interpolateValues(firstRect['position']['x'], secondRect['position']['x'], ratio), 
            'y': interpolateValues(firstRect['position']['y'], secondRect['position']['y'], ratio), 
        },
        'size': {
            'width': interpolateValues(firstRect['size']['width'], secondRect['size']['width'], ratio), 
            'height': interpolateValues(firstRect['size']['height'], secondRect['size']['height'], ratio)
        }
    }

def drawFrameFaceRect(frame, rectIndex, color, face):
    global overlayHash, currFrameIndex, keyFrames

    rectKeyFrame = overlayHash.get(getKey(rectIndex, currFrameIndex))

    if (rectKeyFrame != None):
        drawFaceRect(frame, rectKeyFrame, color, face)
    else:
        lastKeyFrame = getLastKeyFrame(rectIndex)
        if lastKeyFrame != None:
            lastKeyFrameRect = overlayHash.get(getKey(rectIndex, lastKeyFrame));
            nextKeyFrame = getNextKeyFrame(rectIndex)
            if nextKeyFrame != None:
                nextKeyFrameRect = overlayHash.get(getKey(rectIndex, nextKeyFrame));

                drawFaceRect(frame, interpolateRects(lastKeyFrameRect, lastKeyFrame, nextKeyFrameRect, nextKeyFrame, currFrameIndex), map(lambda x: x/2, color), face)

def deleteCurrentKeyFrame():
    global overlayHash, currFrameIndex, currRectIndex

    rectKeyFrame = overlayHash.get(getKey(currRectIndex, currFrameIndex))
    if (rectKeyFrame != None):
        del overlayHash[getKey(currRectIndex, currFrameIndex)]
        loadOverlays(overlayHash.values())

def refreshScroller(frame):
    global frameScrollerX, currFrameIndex, framesNum, overlayHash, keyFrames

    for frameIndex in keyFrames:
        keyFrameX = int(SCROLLER_START_X + float(frameIndex) / framesNum * (SCROLLER_END_X - SCROLLER_START_X))
        cv2.rectangle(frame,(keyFrameX, FRAME_SCROLLER_Y),(keyFrameX + SCROLLER_WIDTH, FRAME_SCROLLER_Y + SCROLLER_HEIGHT),(0,50,0),3)        

    cv2.rectangle(frame,(int(frameScrollerX), FRAME_SCROLLER_Y),(int(frameScrollerX) + SCROLLER_WIDTH, FRAME_SCROLLER_Y + SCROLLER_HEIGHT),(0,126,0),3)

    drawFrameFaceRect(frame, FIRST_RECT_INDEX, (255, 0, 0), None)
    drawFrameFaceRect(frame, SECOND_RECT_INDEX, (0, 0, 255), None)

def setFrameByScroller():
    global currFrameIndex, framesNum

    currFrameIndex = int(float(frameScrollerX - SCROLLER_START_X) / (SCROLLER_END_X - SCROLLER_START_X) * framesNum)

def setScrollerByFrame(frameIndex):
    global frameScrollerX, framesNum

    frameScrollerX = SCROLLER_START_X + float(frameIndex) / framesNum * (SCROLLER_END_X - SCROLLER_START_X)

def updateFrameScrollerX(x):
    global frameScrollerX

    if (x < SCROLLER_START_X):
        frameScrollerX = SCROLLER_START_X
    elif (x > SCROLLER_END_X):
        frameScrollerX = SCROLLER_END_X - 1
    else:
        frameScrollerX = x

    setFrameByScroller()

def handleDrawRectStart(x, y):
    global startX, startY, currRectIndex, currFrameIndex, overlayHash

    startX = x
    startY = y

    key = getKey(currRectIndex, currFrameIndex)
    if overlayHash.get(key) != None:
        overlayHash.get(key)['position']['x'] = x;
        overlayHash.get(key)['position']['y'] = y;
    else:
        # Create new key frame!
        keyFrame = {
            'rectIndex': currRectIndex,
            'keyFrameIndex': currFrameIndex,
            'position': {'x': x, 'y': y},
            'size': {'width': 1, 'height': 1}
        }

        overlayHash[key] = keyFrame

        if (overlayHash.get(getKey((currRectIndex + 1) % 2, currFrameIndex)) == None):
            keyFrames.append(currFrameIndex)
            keyFrames.sort()

def handleDrawRectEnd(x, y):
    global startX, startY, currRectIndex, currFrameIndex, overlayHash

    key = getKey(currRectIndex, currFrameIndex)
    keyFrame = overlayHash.get(key)
    keyFrame['size']['width'] = x - startX
    keyFrame['size']['height'] = y - startY

def onMouseMove(event, x, y, flags, param):
    global editorMode, frame, frameScrollerX, dragStartX, dragStartScrollerX, scriptMode

    if scriptMode == EDIT_MODE:
        if event == cv2.EVENT_LBUTTONDOWN:
            if (y >= FRAME_SCROLLER_Y):
                dragStartX = x
                dragStartScrollerX = frameScrollerX
                editorMode = DRAGGING_FRAME
            else:
                editorMode = DRAWING_RECT
                handleDrawRectStart(x, y)

        elif event == cv2.EVENT_MOUSEMOVE:
            if (editorMode == DRAGGING_FRAME):
                updateFrameScrollerX(dragStartScrollerX + x - dragStartX)
            elif (editorMode == DRAWING_RECT):
                handleDrawRectEnd(x, y)

        elif event == cv2.EVENT_LBUTTONUP:
            if (editorMode == DRAGGING_FRAME):
                editorMode = NONE
                updateFrameScrollerX(dragStartScrollerX + x - dragStartX)
            elif (editorMode == DRAWING_RECT):
                handleDrawRectEnd(x, y)
                editorMode = NONE

def getKey(index, frame):
    return str(frame) + str(index)

def loadOverlays(overlayDef):
    global overlayHash, keyFrames

    keyFrames = []
    keyFramesHash = {}

    for rectKeyFrame in overlayDef:
        overlayHash[getKey(rectKeyFrame['rectIndex'], rectKeyFrame['keyFrameIndex'])] = rectKeyFrame
        if (keyFramesHash.get(rectKeyFrame['keyFrameIndex']) == None):
            keyFrames.append(rectKeyFrame['keyFrameIndex'])
            keyFramesHash[rectKeyFrame['keyFrameIndex']] = 1
    keyFrames.sort()

def setFrameToNextKeyFrame():
    global currFrameIndex, keyFrames

    nextKeyFrame = getNextKeyFrame()
    if (nextKeyFrame != None):
        currFrameIndex = nextKeyFrame

def getLastKeyFrame(rectIndex = None):
    global currFrameIndex, keyFrames, overlayHash

    for i in range(len(keyFrames) - 1, -1, -1):
        if (keyFrames[i] < currFrameIndex) and (rectIndex is None or overlayHash.get(getKey(rectIndex, keyFrames[i])) is not None):
            return keyFrames[i]

    return None

def getNextKeyFrame(rectIndex = None):
    global currFrameIndex, keyFrames

    for i in range(len(keyFrames)):
        if (keyFrames[i] > currFrameIndex) and (rectIndex is None or overlayHash.get(getKey(rectIndex, keyFrames[i])) is not None):
            return keyFrames[i]

    return None

def setFrameToLastKeyFrame():
    global currFrameIndex

    lastKeyFrame = getLastKeyFrame()
    if (lastKeyFrame != None):
        currFrameIndex = lastKeyFrame

def drawCurrColor():
    global currRectIndex, frame

    color = (255, 0, 0) if currRectIndex == 0 else (0, 0, 255)
    cv2.circle(frame, (30, 150), 15, color ,3)

def getFaces():
    global face1, face2

    face1 = cameraImage[133:133+140, 435:435+80]
    face2 = cameraImage[281:281+114, 114:114+71]

scriptMode = RUN_MODE
if (len(sys.argv) == 2):
    scriptMode = sys.argv[1]

startX = 0
startY = 0

overlayHash = {}
keyFrames = []

try:
    with open('imabean.json') as jsonFile:  
        overlayDef = json.load(jsonFile)
except:
    overlayDef = []

loadOverlays(overlayDef)

dragStartX = 0
dragStartScrollerX = SCROLLER_START_X
editorMode = NONE

cap = cv2.VideoCapture('./master_converted.mp4')
framesNum = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

cameraImage = cv2.imread("camera-stream.jpg")
face1 = None
face2 = None

window_name = 'projector'
cv2.namedWindow(window_name)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setMouseCallback(window_name, onMouseMove)

currRectIndex = 0
currFrameIndex = 0
frameScrollerX = float(SCROLLER_START_X)

nextFrame = True

while True:
    if scriptMode == EDIT_MODE:
        cap.set(cv2.CAP_PROP_POS_FRAMES, currFrameIndex)

    ret, frame = cap.read()

    if scriptMode == EDIT_MODE:
        refreshScroller(frame)
        drawCurrColor()

    if scriptMode == RUN_MODE:
        getFaces()
        drawFrameFaceRect(frame, FIRST_RECT_INDEX, (255, 0, 0), face1)
        drawFrameFaceRect(frame, SECOND_RECT_INDEX, (0, 0, 255), face2)

        # Get current face positions

        # Crop live stream of camera

        # Draw faces on image

    cv2.imshow(window_name, frame)

    k = cv2.waitKey(33)#cv2.waitKey(1) & 0xFF
    if k==27: # Esc key to stop
        break

    if scriptMode == EDIT_MODE:
        if k==-1:  # normally -1 returned,so don't print it
            continue
        elif k == 2: # Left key
            if currFrameIndex > 0:
                currFrameIndex = currFrameIndex - 1
                setScrollerByFrame(currFrameIndex)
        elif k == 3: # Right key
            if currFrameIndex < framesNum - 1:
                currFrameIndex = currFrameIndex + 1
                setScrollerByFrame(currFrameIndex)
        elif k == ord('m'):
            setFrameToNextKeyFrame()
            setScrollerByFrame(currFrameIndex)
        elif k == ord('n'):
            setFrameToLastKeyFrame()
            setScrollerByFrame(currFrameIndex)
        elif k == ord('c'):
            currRectIndex = (currRectIndex + 1) % 2
        elif k == ord('p'):
            scriptMode = RUN_MODE
        elif k == ord('d'):
            deleteCurrentKeyFrame()
        elif k == ord('S'):
            print overlayHash.values()
            with open('imabean.json', 'w') as outfile:
                json.dump(overlayHash.values(), outfile)
    else:
        if k == ord('s'):
            scriptMode = EDIT_MODE
            setScrollerByFrame(currFrameIndex)

    if scriptMode == RUN_MODE:
        currFrameIndex = currFrameIndex + 1

cap.release()
cv2.destroyAllWindows()
