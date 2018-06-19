import numpy as np
import cv2
import random
import sys
import json

#from ffpyplayer.player import MediaPlayer

RUN_MODE = 'run'
TEST_MODE = 'test'
EDIT_MODE = 'edit'

NONE = 0
DRAGGING_FRAME = 1
DRAWING_RECT = 2
DRAGGING_RECT = 3
MOVING_RECT = 4

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

FIRST_FACE_X = 445
FIRST_FACE_Y = 143
FIRST_FACE_WIDTH = 85
FIRST_FACE_HEIGHT = 124

SECOND_FACE_X = 119
SECOND_FACE_Y = 296
SECOND_FACE_WIDTH = 100
SECOND_FACE_HEIGHT = 138

def resizeNoStretch(image, newWidth, newHeight):
    oldRows, oldCols = image.shape[:2]
    print("Old rows/cols: ", oldRows, oldCols)

    print("new width/height: ", newWidth, newHeight)
    resizeTarget = np.zeros((newHeight, newWidth, 3), np.float)
    resizeRows, resizeCols = resizeTarget.shape[:2]
    print("Resize rows/cols: ", resizeRows, resizeCols)

    offsetX = int((newWidth - oldCols) / 2.0)
    offsetY = int((newHeight - oldRows) / 2.0)
    print("Offset x/y: ", offsetX, offsetY)

    print("Dest: ", offsetX, offsetX + oldCols)
    resizeTarget[offsetY : offsetY + oldRows, offsetX : offsetX + oldCols] = image
    return resizeTarget

def drawFaceRect(frame, rectKeyFrame, color, face):
    global alpha1, alpha2, scriptMode

    start = (int(rectKeyFrame['position']['x']), int(rectKeyFrame['position']['y']))
    end = (int(rectKeyFrame['position']['x'] + rectKeyFrame['size']['width']), int(rectKeyFrame['position']['y'] + rectKeyFrame['size']['height']))

    if scriptMode != RUN_MODE:
        drawRotatedRect(frame, start, end, color, 3, rectKeyFrame['position']['rotation'])

    #Draw crop from camera
    if (face is not None):

        # First, resize face to designated rectangle size, get new size
        stretchedFace = cv2.resize(face, (int(rectKeyFrame['size']['width']), int(rectKeyFrame['size']['height'])), interpolation = cv2.INTER_AREA)
        rows, cols = stretchedFace.shape[:2]

        # Now, load alpha mask, and resize it to same size
        alpha = alpha1 if rectKeyFrame['rectIndex'] == 0 else alpha2
        alpha = cv2.resize(alpha, (int(rectKeyFrame['size']['width']), int(rectKeyFrame['size']['height'])), interpolation = cv2.INTER_AREA)

        # Resize both face and mask to allow rotation without cropping
        print("Resize face")
        stretchedFace = resizeNoStretch(stretchedFace, int(cols * 3), int(rows * 3))
        print("Resize alpha")
        alpha = resizeNoStretch(alpha, int(cols * 3), int(rows * 3))
        postResizeRows = int(rows * 3)
        postResizeCols = int(cols * 3)

        # Rotate face to correct rotation
        M = cv2.getRotationMatrix2D((postResizeCols/2,postResizeRows/2), rectKeyFrame['position']['rotation'] / (np.pi * 2) * 360, 1)
        stretchedFace = cv2.warpAffine(stretchedFace, M, (postResizeCols,postResizeRows))

        # Rotate mask to match face rotation
        alpha = cv2.warpAffine(alpha, M, (postResizeCols,postResizeRows))

        # Apply mask on face (foreground)
        foreground = stretchedFace
        alpha = alpha / 255
        foreground = cv2.multiply(alpha, foreground)

        backgroundX = int(rectKeyFrame['position']['x']) - int((postResizeCols - cols) / 2.0)
        backgroundY = int(rectKeyFrame['position']['y']) - int((postResizeRows - rows) / 2.0)

        # Get background from image
        sourceYOffset = 0
        if backgroundY < 0:
            sourceYOffset = abs(backgroundY)
            backgroundY = 0

        background = frame[backgroundY : backgroundY + postResizeRows - sourceYOffset, backgroundX : backgroundX + postResizeCols].astype(float)
        alpha = alpha[0 : postResizeRows - sourceYOffset, 0 : postResizeCols]
        print("Alpha: ", len(alpha), "Background: ", len(background))
        background = cv2.multiply((1.0 - alpha), background)
        foreground = foreground[0 : postResizeRows - sourceYOffset, 0 : postResizeCols]
        outImage = cv2.add(foreground, background)

        frame[backgroundY : backgroundY + postResizeRows - sourceYOffset, backgroundX : backgroundX + postResizeCols] = outImage[0 : postResizeRows - sourceYOffset, 0 : postResizeCols]

def drawRotatedRect(frame, start, end, color, line, rotation):
    points = [start, (start[0], end[1]), end, (end[0], start[1])]
    centerX = (start[0] + end[0]) / 2.0
    centerY = (start[1] + end[1]) / 2.0

    rotatedPoints = list(map(lambda point: rotatePointAroundPoint(point, (centerX, centerY), rotation), points))
    rotatedCoordinates = list(map(lambda tuple: [tuple[0], tuple[1]], rotatedPoints))

    npPoints = np.array(rotatedCoordinates, np.int32)
    npPoints = npPoints.reshape((-1, 1, 2))
    cv2.polylines(frame, [npPoints], True, color, line)

def rotatePointAroundPoint(point, anchor, angle):
    (x, y) = point
    y = SCREEN_HEIGHT - y
    (anchorX, anchorY) = anchor
    anchorY = SCREEN_HEIGHT - anchorY

    s = np.sin(angle)
    c = np.cos(angle)

    (dx, dy) = (x - anchorX, y - anchorY)

    rotatedDx = dx * c - dy * s
    rotatedDy = dy * c + dx * s

    return (anchorX + rotatedDx, SCREEN_HEIGHT - (anchorY + rotatedDy))

def interpolateValues(first, second, ratio):
    return (first + (second - first) * ratio)

def interpolateRects(firstRect, firstFrame, secondRect, secondFrame, currFrame):
    framesDiff = secondFrame - firstFrame
    ratio = float(currFrame - firstFrame) / framesDiff;
    return {
        'rectIndex': firstRect['rectIndex'],
        'position': {
            'x': interpolateValues(firstRect['position']['x'], secondRect['position']['x'], ratio), 
            'y': interpolateValues(firstRect['position']['y'], secondRect['position']['y'], ratio), 
            'rotation': interpolateValues(firstRect['position']['rotation'], secondRect['position']['rotation'], ratio), 
        },
        'size': {
            'width': interpolateValues(firstRect['size']['width'], secondRect['size']['width'], ratio), 
            'height': interpolateValues(firstRect['size']['height'], secondRect['size']['height'], ratio)
        }
    }

def getInterpolatedRect(rectIndex):
    global overlayHash, currFrameIndex, scriptMode

    lastKeyFrame = getLastKeyFrame(rectIndex)
    if lastKeyFrame != None:
        lastKeyFrameRect = overlayHash.get(getKey(rectIndex, lastKeyFrame));
        nextKeyFrame = getNextKeyFrame(rectIndex)
        if nextKeyFrame != None:
            nextKeyFrameRect = overlayHash.get(getKey(rectIndex, nextKeyFrame));
            return interpolateRects(lastKeyFrameRect, lastKeyFrame, nextKeyFrameRect, nextKeyFrame, currFrameIndex)
        elif scriptMode == EDIT_MODE:
            return lastKeyFrameRect

    return None

def drawFrameFaceRect(frame, rectIndex, color, face):
    global overlayHash, currFrameIndex

    rectKeyFrame = overlayHash.get(getKey(rectIndex, currFrameIndex))

    if (rectKeyFrame != None):
        drawFaceRect(frame, rectKeyFrame, color, face)
    else:
        rect = getInterpolatedRect(rectIndex)

        if (rect is not None):
            drawFaceRect(frame, rect, list(map(lambda x: x/2, color)), face)

def convertToKeyFrame():
    global overlayHash, currRectIndex, currFrameIndex, keyFrames

    keyFrame = overlayHash.get(getKey(currRectIndex, currFrameIndex))

    if (keyFrame is None):
        rect = getInterpolatedRect(currRectIndex)
        if (rect is not None):
            createKeyFrame(rect['position']['x'], rect['position']['y'], rect['size']['width'], rect['size']['height'])

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

def createKeyFrame(x, y, width, height):
    global currRectIndex, currFrameIndex

    keyFrame = {
        'rectIndex': currRectIndex,
        'keyFrameIndex': currFrameIndex,
        'position': {'x': x, 'y': y, 'rotation': 0},
        'size': {'width': width, 'height': height}
    }

    key = getKey(currRectIndex, currFrameIndex)
    overlayHash[key] = keyFrame

    if (overlayHash.get(getKey((currRectIndex + 1) % 2, currFrameIndex)) == None):
        keyFrames.append(currFrameIndex)
        keyFrames.sort()

def handleDragRectStart(x, y):
    global startX, startY, startRectX, startRectY, overlayHash, pointedRect

    startX = x
    startY = y

    startRectX = pointedRect['position']['x']
    startRectY = pointedRect['position']['y']

    key = getKey(currRectIndex, currFrameIndex)
    if overlayHash.get(key) is None:
        createKeyFrame(startRectX, startRectY, pointedRect.width, pointedRect.height)

def handleDragRectEnd(x, y):
    global startX, startY, startRectX, startRectY, currRectIndex, currFrameIndex, overlayHash

    key = getKey(currRectIndex, currFrameIndex)
    keyFrame = overlayHash.get(key)
    keyFrame['position']['x'] = startRectX + x - startX
    keyFrame['position']['y'] = startRectY + y - startY    

def handleDrawRectStart(x, y):
    global startX, startY, currRectIndex, currFrameIndex, overlayHash

    startX = x
    startY = y

    key = getKey(currRectIndex, currFrameIndex)
    if overlayHash.get(key) is not None:
        overlayHash.get(key)['position']['x'] = x;
        overlayHash.get(key)['position']['y'] = y;
        overlayHash.get(key)['position']['rotation'] = 0
    else:
        createKeyFrame(x, y, 1, 1)

def handleDrawRectEnd(x, y):
    global startX, startY, currRectIndex, currFrameIndex, overlayHash

    key = getKey(currRectIndex, currFrameIndex)
    keyFrame = overlayHash.get(key)
    keyFrame['size']['width'] = x - startX
    keyFrame['size']['height'] = y - startY

def isOnRect(x, y, index):
    global currFrameIndex

    key = getKey(index, currFrameIndex)
    keyFrame = overlayHash.get(key)

    if (keyFrame is not None):
        rectX = keyFrame['position']['x']
        rectY = keyFrame['position']['y']
        rectWidth = keyFrame['size']['width']
        rectHeight = keyFrame['size']['height']

        if (x >= rectX and x <= rectX + rectWidth and y >= rectY and y <= rectY + rectHeight):
            return keyFrame

    return None


def getPointedRect(x, y):
    global currRectIndex, currFrameIndex

    rect = isOnRect(x, y, currRectIndex)

    if (rect is not None):
        return rect

    rect = isOnRect(x, y, (currRectIndex + 1) % 2)

    if (rect is not None):
        return rect

    return None

def onMouseMove(event, x, y, flags, param):
    global editorMode, frame, frameScrollerX, dragStartX, dragStartScrollerX, scriptMode, currRectIndex, pointedRect

    if scriptMode == EDIT_MODE:
        if event == cv2.EVENT_LBUTTONDOWN:
            if (y >= FRAME_SCROLLER_Y):
                dragStartX = x
                dragStartScrollerX = frameScrollerX
                editorMode = DRAGGING_FRAME
            else:
                pointedRect = getPointedRect(x, y)
                if (pointedRect is None):
                    editorMode = DRAWING_RECT
                    handleDrawRectStart(x, y)
                else:
                    currRectIndex = pointedRect['rectIndex']
                    editorMode = DRAGGING_RECT
                    handleDragRectStart(x, y)

        elif event == cv2.EVENT_MOUSEMOVE:
            if (editorMode == DRAGGING_FRAME):
                updateFrameScrollerX(dragStartScrollerX + x - dragStartX)
            elif (editorMode == DRAWING_RECT):
                handleDrawRectEnd(x, y)
            elif (editorMode == DRAGGING_RECT):
                handleDragRectEnd(x, y)

        elif event == cv2.EVENT_LBUTTONUP:
            if (editorMode == DRAGGING_FRAME):
                editorMode = NONE
                updateFrameScrollerX(dragStartScrollerX + x - dragStartX)
            elif (editorMode == DRAWING_RECT):
                handleDrawRectEnd(x, y)
                editorMode = NONE
            elif (editorMode == DRAGGING_RECT):
                handleDragRectEnd(x, y)
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

    face1 = cameraImage[FIRST_FACE_Y:FIRST_FACE_Y+FIRST_FACE_HEIGHT, FIRST_FACE_X:FIRST_FACE_X+FIRST_FACE_WIDTH]
    face2 = cameraImage[SECOND_FACE_Y:SECOND_FACE_Y+SECOND_FACE_HEIGHT, SECOND_FACE_X:SECOND_FACE_X+SECOND_FACE_WIDTH]

def isRunMode():
    global scriptMode

    return (scriptMode == RUN_MODE or scriptMode == TEST_MODE)

scriptMode = RUN_MODE
if (len(sys.argv) == 2):
    scriptMode = sys.argv[1]

startX = 0
startY = 0

startRectX = 0
startRectY = 0

pointedRect = None

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

player = None
if isRunMode:
    pass
    #player = MediaPlayer('./master_converted.mp4')

if scriptMode == RUN_MODE:
    camera = cv2.VideoCapture(0)
framesNum = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

if scriptMode == TEST_MODE:
    cameraImage = cv2.imread('./camera-stream.jpg')

alpha1 = cv2.imread('first-alpha-mask.png').astype(np.float)
alpha2 = cv2.imread('second-alpha-mask.png').astype(np.float)

face1 = None
face2 = None

window_name = 'projector'

if isRunMode():
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
else:
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

    if player is not None:
        player.get_frame()

    if scriptMode == RUN_MODE:
        retCamera, cameraImage = camera.read()

    if scriptMode == EDIT_MODE:
        refreshScroller(frame)
        drawCurrColor()

    if isRunMode():
        getFaces()
        drawFrameFaceRect(frame, FIRST_RECT_INDEX, (255, 0, 0), face1)
        drawFrameFaceRect(frame, SECOND_RECT_INDEX, (0, 0, 255), face2)

    cv2.imshow(window_name, frame)

    k = cv2.waitKey(33)
    if k==27: # Esc key to stop
        break

    if scriptMode == EDIT_MODE:
        if k == -1:  # normally -1 returned, so don't print it
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
        elif k == ord('K'):
            convertToKeyFrame()
        elif k == ord('c'):
            currRectIndex = (currRectIndex + 1) % 2
        elif k == ord('p'):
            scriptMode = TEST_MODE
        elif k == ord('d'):
            deleteCurrentKeyFrame()
        elif k == ord('S'):
            with open('imabean.json', 'w') as outfile:
                json.dump(list(overlayHash.values()), outfile)

        keyFrame = overlayHash.get(getKey(currRectIndex, currFrameIndex))
        if keyFrame is not None:
            if k == ord('x'):
                keyFrame['position']['x'] -= 1
            elif k == ord('X'):
                keyFrame['position']['x'] += 1
            elif k == ord('y'):
                keyFrame['position']['y'] -= 1
            elif k == ord('Y'):
                keyFrame['position']['y'] += 1
            elif k == ord('w'):
                keyFrame['size']['width'] -= 1
            elif k == ord('W'):
                keyFrame['size']['width'] += 1
            elif k == ord('h'):
                keyFrame['size']['height'] -= 1
            elif k == ord('H'):
                keyFrame['size']['height'] += 1
            elif k == ord('r'):
                keyFrame['position']['rotation'] -= (2 * np.pi / 360.0)
            elif k == ord('R'):
                keyFrame['position']['rotation'] += (2 * np.pi / 360.0)

    else:
        if k == ord('s'):
            scriptMode = EDIT_MODE
            setScrollerByFrame(currFrameIndex)

    if isRunMode():
        currFrameIndex = currFrameIndex + 1
        if currFrameIndex >= framesNum:
            currFrameIndex = 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, currFrameIndex)

cap.release()
cv2.destroyAllWindows()
exit()

