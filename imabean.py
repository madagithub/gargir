import numpy as np
import cv2
import random

NONE = 0
DRAGGING_FRAME = 1
DRAWING_FIRST_RECT = 2
DRAWING_SECOND_RECT = 3
MOVING_FIRST_RECT = 4
MOVING_SECOND_RECT = 5

SINGLE_FRAME = 0
LINEAR_MOVEMENT = 1

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

def drawFaceRect(frame, rectKeyFrame, color):
    if (rectKeyFrame != None):
        frame = cv2.rectangle(frame, (rectKeyFrame['position']['x'], rectKeyFrame['position']['y']), 
            (rectKeyFrame['position']['x'] + rectKeyFrame['size']['width'], rectKeyFrame['position']['y'] + rectKeyFrame['size']['height']), color ,3)
    return frame

def refreshScroller(frame):
    global frameScrollerX, currFrameIndex, framesNum, overlayHash, keyFrames

    for frameIndex in keyFrames:
        keyFrameX = int(SCROLLER_START_X + float(frameIndex) / framesNum * (SCROLLER_END_X - SCROLLER_START_X))
        frame = cv2.rectangle(frame,(keyFrameX, FRAME_SCROLLER_Y),(keyFrameX + SCROLLER_WIDTH, FRAME_SCROLLER_Y + SCROLLER_HEIGHT),(0,50,0),3)        

    currFrameIndex = int(float(frameScrollerX - SCROLLER_START_X) / (SCROLLER_END_X - SCROLLER_START_X) * framesNum)
    frame = cv2.rectangle(frame,(frameScrollerX, FRAME_SCROLLER_Y),(frameScrollerX + SCROLLER_WIDTH, FRAME_SCROLLER_Y + SCROLLER_HEIGHT),(0,126,0),3)

    firstRect = overlayHash.get(getKey(FIRST_RECT_INDEX, currFrameIndex))
    secondRect = overlayHash.get(getKey(SECOND_RECT_INDEX, currFrameIndex))

    frame = drawFaceRect(frame, firstRect, (255, 0, 0))
    frame = drawFaceRect(frame, secondRect, (0, 0, 255))

    return frame

def updateFrameScrollerX(x):
    global frameScrollerX

    if (x < SCROLLER_START_X):
        frameScrollerX = SCROLLER_START_X
    elif (x > SCROLLER_END_X):
        frameScrollerX = SCROLLER_END_X - 1
    else:
        frameScrollerX = x

def onMouseMove(event, x, y, flags, param):
    global editorMode, frame, frameScrollerX, dragStartX, dragStartScrollerX

    if event == cv2.EVENT_LBUTTONDOWN:
        if (y >= FRAME_SCROLLER_Y):
            dragStartX = x
            dragStartScrollerX = frameScrollerX
            editorMode = DRAGGING_FRAME            

    elif event == cv2.EVENT_MOUSEMOVE:
        if (editorMode == DRAGGING_FRAME):
            updateFrameScrollerX(dragStartScrollerX + x - dragStartX)

    elif event == cv2.EVENT_LBUTTONUP:
        if (editorMode == DRAGGING_FRAME):
            editorMode = NONE
            updateFrameScrollerX(dragStartScrollerX + x - dragStartX)

def getKey(index, frame):
    return str(frame) + str(index)

def loadOverlays(overlayDef):
    global overlayHash, keyFrames

    keyFramesHash = {}

    for rectKeyFrame in overlayDef:
        overlayHash[getKey(rectKeyFrame['rectIndex'], rectKeyFrame['keyFrameIndex'])] = rectKeyFrame
        if (keyFramesHash.get(rectKeyFrame['keyFrameIndex']) == None):
            keyFrames.append(rectKeyFrame['keyFrameIndex'])
            keyFramesHash[rectKeyFrame['keyFrameIndex']] = 1

    print keyFrames

overlayDef = [
    {
        'rectIndex': 0,
        'position': {'x': 200, 'y': 200},
        'size': {'width': 100, 'height': 100},
        'keyFrameIndex': 0,
        'transition': SINGLE_FRAME
    },
    {
        'rectIndex': 1,
        'position': {'x': 350, 'y': 350},
        'size': {'width': 50, 'height': 50},
        'keyFrameIndex': 0,
        'transition': SINGLE_FRAME
    },

    {
        'rectIndex': 0,
        'position': {'x': 200, 'y': 200},
        'size': {'width': 100, 'height': 100},
        'keyFrameIndex': 50,
        'transition': LINEAR_MOVEMENT
    },
    {
        'rectIndex': 1,
        'position': {'x': 350, 'y': 350},
        'size': {'width': 50, 'height': 50},
        'keyFrameIndex': 50,
        'transition': LINEAR_MOVEMENT
    }
]

overlayHash = {}
keyFrames = []
loadOverlays(overlayDef)

dragStartX = 0
dragStartScrollerX = SCROLLER_START_X
editorMode = NONE

cap = cv2.VideoCapture('/Users/idankimel/Dev/ScienceMuseum/Bean/master_converted.mp4')
framesNum = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

window_name = 'projector'
cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
#cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setMouseCallback(window_name, onMouseMove)

currFrameIndex = 100
frameScrollerX = SCROLLER_START_X

firstX = random.randint(0, 1920 - 100)
firstY = random.randint(0, 1080 - 200)

secondX = random.randint(0, 1920 - 100)
secondY = random.randint(0, 1080 - 200)

nextFrame = True

while True:
    cap.set(cv2.CAP_PROP_POS_FRAMES, currFrameIndex)
    ret, frame = cap.read()

    frame = refreshScroller(frame)

    # First face, randomize coordinate change for testing
    #firstX += random.randint(-1, 1)
    #firstY += random.randint(-1, 1)
    #frame = cv2.rectangle(frame,(firstX, firstY),(firstX + 100, firstY + 200),(255,0,0),3)

    # Second face, randomize coordinate change for testing
    #secondX += random.randint(-1, 1)
    #secondY += random.randint(-1, 1)
    #frame = cv2.rectangle(frame,(secondX, secondY),(secondX + 100, secondY + 200),(0,255,0),3)

    cv2.imshow(window_name, frame)

    k = cv2.waitKey(1) & 0xFF
    if k == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
