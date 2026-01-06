import cv2 as cv
import os
import numpy as np
import matplotlib.pyplot as plt
from tracker import Tracker
from paramsJsonParse import TrackerParams

jsonPath = os.path.join('/','home','avivi','Developer','Python','OpenCV','video','samples_params.json')

trckerParams = TrackerParams()
trckerParams.parse(jsonPath)
sample = 'highway_1.mp4'

params = trckerParams.convertRoiByKey(sample)
path = trckerParams.path
print(params)

videoPath = os.path.join(path,sample)

# Define tracker
tracker = Tracker()

cap = cv.VideoCapture(videoPath)

# Capture Properties
hight = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
print(hight, width)

# Object detect (stable camera)
objDetector = cv.createBackgroundSubtractorMOG2(history=100, 
                                                varThreshold=params['DetectorThd'])

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Extract ROI
    h_st, h_en, w_st, w_end = params['FrameRoi']
    roi = frame[h_st :h_en, w_st: w_end]

    # Object detection
    masked = objDetector.apply(roi)
    _, masked = cv.threshold(masked, thresh=254, maxval=255, type=cv.THRESH_BINARY)
    contours, _ = cv.findContours(masked, mode=cv.RETR_TREE, method=cv.CHAIN_APPROX_SIMPLE)
    detection = []
    for cnt in contours:
        # filter out small countors
        area = cv.contourArea(cnt)
        if area > params['CountoursArea']:
            rect = cv.boundingRect(cnt)
            #cv.rectangle(roi, pt1=(x,y), pt2=(x+w, y+h), color=(0,255,0), thickness=3)
            #cv.drawContours(roi, contours=[cnt], contourIdx=-1, color=(0,255,0), thickness=2)
            detection.append(rect)
    
    # Object Tracking
    if detection: # if not empty list then objects detected 
        bb_ids = tracker.update(detection)
        for (id, obj) in bb_ids.items():
            x,y,w,h = obj
            # set label (object id) on bounding_box 
            cv.putText(roi, 
                       text=str(id), 
                       org=(x,y-params['BoxYOffset']), 
                       fontFace=cv.FONT_HERSHEY_PLAIN, 
                       fontScale=2,
                       color=(0,255,0),
                       thickness=2)
            # drew new rect sournding detected object by tracker
            cv.rectangle(roi, pt1=(x,y), pt2=(x+w, y+h), color=(0,255,0), thickness=3)


    cv.imshow('MASK', masked)
    cv.imshow('ROI', roi)
    cv.imshow('Frame', frame)

    if cv.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv.destroyAllWindows()
