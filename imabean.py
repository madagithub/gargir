import numpy as np
import cv2
import random

def nothing(x):
  pass

cap = cv2.VideoCapture('/Users/idankimel/Dev/ScienceMuseum/Bean/master_converted.mp4')
framesNum = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

editor_window_name = 'editor'
cv2.namedWindow(editor_window_name, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(editor_window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

window_name = 'projector'
cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

cv2.createTrackbar('Frame', editor_window_name, 1, framesNum, nothing)

firstX = random.randint(0, 1920 - 100)
firstY = random.randint(0, 1080 - 200)

secondX = random.randint(0, 1920 - 100)
secondY = random.randint(0, 1080 - 200)

nextFrame = True

while(True):
    cap.set(cv2.CAP_PROP_POS_FRAMES, cv2.getTrackbarPos('Frame', window_name))
    ret, frame = cap.read()

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
