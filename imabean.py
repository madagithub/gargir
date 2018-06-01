import numpy as np
import cv2
import random

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

def drawFaceRect(frame, rectKeyFrame, color):
    start = (rectKeyFrame['position']['x'], rectKeyFrame['position']['y'])
    end = (rectKeyFrame['position']['x'] + rectKeyFrame['size']['width'], rectKeyFrame['position']['y'] + rectKeyFrame['size']['height'])

    cv2.rectangle(frame, start, end, color ,3)

    #text = 'Single' if rectKeyFrame['transition'] == SINGLE_FRAME else 'Linear'
    #y = 150 if rectKeyFrame['rectIndex'] == 1 else 180
    #cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

def drawFrameFaceRect(frame, rectIndex, color):
    global overlayHash

    rectKeyFrame = overlayHash.get(getKey(rectIndex, currFrameIndex))

    if (rectKeyFrame != None):
        drawFaceRect(frame, rectKeyFrame, color)
    else:
        lastKeyFrame = getLastKeyFrame()
        if lastKeyFrame != None:
            lastKeyFrameRect = overlayHash.get(getKey(rectIndex, lastKeyFrame));
            if lastKeyFrameRect != None:
                drawFaceRect(frame, lastKeyFrameRect, color)

def refreshScroller(frame):
    global frameScrollerX, currFrameIndex, framesNum, overlayHash, keyFrames

    for frameIndex in keyFrames:
        keyFrameX = int(SCROLLER_START_X + float(frameIndex) / framesNum * (SCROLLER_END_X - SCROLLER_START_X))
        cv2.rectangle(frame,(keyFrameX, FRAME_SCROLLER_Y),(keyFrameX + SCROLLER_WIDTH, FRAME_SCROLLER_Y + SCROLLER_HEIGHT),(0,50,0),3)        

    cv2.rectangle(frame,(int(frameScrollerX), FRAME_SCROLLER_Y),(int(frameScrollerX) + SCROLLER_WIDTH, FRAME_SCROLLER_Y + SCROLLER_HEIGHT),(0,126,0),3)

    drawFrameFaceRect(frame, FIRST_RECT_INDEX, (255, 0, 0))
    drawFrameFaceRect(frame, SECOND_RECT_INDEX, (0, 0, 255))

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
    global editorMode, frame, frameScrollerX, dragStartX, dragStartScrollerX

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

    keyFramesHash = {}

    for rectKeyFrame in overlayDef:
        overlayHash[getKey(rectKeyFrame['rectIndex'], rectKeyFrame['keyFrameIndex'])] = rectKeyFrame
        if (keyFramesHash.get(rectKeyFrame['keyFrameIndex']) == None):
            keyFrames.append(rectKeyFrame['keyFrameIndex'])
            keyFramesHash[rectKeyFrame['keyFrameIndex']] = 1

def setFrameToNextKeyFrame():
    global currFrameIndex, keyFrames

    for i in range(0, len(keyFrames)):
        if (keyFrames[i] > currFrameIndex):
            currFrameIndex = keyFrames[i]
            break

def getLastKeyFrame():
    global currFrameIndex, keyFrames

    for i in range(len(keyFrames) - 1, -1, -1):
        if (keyFrames[i] < currFrameIndex):
            return keyFrames[i]

    return None

def setFrameToLastKeyFrame():
    global currFrameIndex

    lastKeyFrame = getLastKeyFrame()
    print 'Last key frame: ', lastKeyFrame
    if (lastKeyFrame != None):
        currFrameIndex = lastKeyFrame

def drawCurrColor():
    global currRectIndex, frame

    color = (255, 0, 0) if currRectIndex == 0 else (0, 0, 255)
    cv2.circle(frame, (30, 150), 15, color ,3)

overlayDef = [
    {
        'rectIndex': 0,
        'position': {'x': 200, 'y': 200},
        'size': {'width': 100, 'height': 100},
        'keyFrameIndex': 0#,
        #'transition': SINGLE_FRAME
    },
    {
        'rectIndex': 1,
        'position': {'x': 350, 'y': 350},
        'size': {'width': 50, 'height': 50},
        'keyFrameIndex': 0#,
        #'transition': SINGLE_FRAME
    },

    {
        'rectIndex': 0,
        'position': {'x': 200, 'y': 300},
        'size': {'width': 100, 'height': 100},
        'keyFrameIndex': 50#,
        #'transition': LINEAR_MOVEMENT
    },
    {
        'rectIndex': 1,
        'position': {'x': 500, 'y': 500},
        'size': {'width': 50, 'height': 50},
        'keyFrameIndex': 50#,
        #'transition': LINEAR_MOVEMENT
    }
]

startX = 0
startY = 0

overlayHash = {}
keyFrames = []
loadOverlays(overlayDef)

dragStartX = 0
dragStartScrollerX = SCROLLER_START_X
editorMode = NONE

cap = cv2.VideoCapture('/Users/idankimel/Dev/ScienceMuseum/Bean/master_converted.mp4')
framesNum = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

window_name = 'projector'
cv2.namedWindow(window_name)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setMouseCallback(window_name, onMouseMove)

currRectIndex = 0
currFrameIndex = 0
frameScrollerX = float(SCROLLER_START_X)

firstX = random.randint(0, 1920 - 100)
firstY = random.randint(0, 1080 - 200)

secondX = random.randint(0, 1920 - 100)
secondY = random.randint(0, 1080 - 200)

nextFrame = True

while True:
    cap.set(cv2.CAP_PROP_POS_FRAMES, currFrameIndex)
    ret, frame = cap.read()

    refreshScroller(frame)

    drawCurrColor()

    # First face, randomize coordinate change for testing
    #firstX += random.randint(-1, 1)
    #firstY += random.randint(-1, 1)
    #frame = cv2.rectangle(frame,(firstX, firstY),(firstX + 100, firstY + 200),(255,0,0),3)

    # Second face, randomize coordinate change for testing
    #secondX += random.randint(-1, 1)
    #secondY += random.randint(-1, 1)
    #frame = cv2.rectangle(frame,(secondX, secondY),(secondX + 100, secondY + 200),(0,255,0),3)

    cv2.imshow(window_name, frame)

    k = k = cv2.waitKey(33)#cv2.waitKey(1) & 0xFF
    if k==27: # Esc key to stop
        break
    elif k==-1:  # normally -1 returned,so don't print it
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
    else:
        print k # else print its value

cap.release()
cv2.destroyAllWindows()
