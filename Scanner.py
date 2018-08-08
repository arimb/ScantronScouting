import cv2
import numpy as np
import math
import configparser
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog

# INTERPRET SCANTRON VALUE
def single(values):
    for i, value in enumerate(reversed(values)):
        if value:
            return str(len(values)-i-1) + ","
    return ","
def multiple(values):
    tmp = ""
    for i, value in enumerate(values, start=1):
        tmp += str(i) + "/" if value else ""
    return tmp[:-1] + ","
def binary(values):
    return str(sum(2**i for i, v in enumerate(values) if v)) + ","
def tf(values):
    return str(values[0]) + ","

# DRAW DOT ON IMAGE, ADD POSITION TO LIST
def drawdot(x,y, cont, flag):
    x_ = x + .5
    y_ = y + (1.5 if slope < 0 else .5)
    x0 = top[0] + int(math.sin(slope)*height/19*y_ + math.cos(-slope)*width/13*x_)
    y0 = top[1] + int(math.cos(slope)*height/19*y_ + (bottom[3] if slope > 0 else 0) + math.sin(-slope)*width/13*x_)
    if flag:
        positions.append((x, y, x0, y0))
        values[y][x] = mod[y0, x0] > 20
    cv2.line(cont, (x0, y0), (x0+1, y0+1), (0,255,0) if values[y][x] else (255,0,255), 2)
# HANDLE CLICK EVENTS
def click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        min = math.sqrt(np.shape(cont)[0]**2 + np.shape(cont)[1]**2)
        minp = (0,0)
        for p in positions:
            if math.sqrt((p[2]-x)**2 + (p[3]-y)**2) < min:
                min = math.sqrt((p[2]-x)**2 + (p[3]-y)**2)
                minp = (p[0], p[1])
        values[minp[1]][minp[0]] = not values[minp[1]][minp[0]]
        drawdot(minp[0], minp[1], cont, False)
        cv2.imshow('img', cont)

# IMPORT IMAGE
tk.Tk().withdraw()
img = cv2.imread(filedialog.askopenfilename(), cv2.IMREAD_GRAYSCALE)
if np.shape(img)[1] > tk.Tk().winfo_screenheight():
    img = cv2.resize(img, None, fx=tk.Tk().winfo_screenheight()/np.shape(img)[1]*.8, fy=tk.Tk().winfo_screenheight()/np.shape(img)[1]*.8, interpolation = cv2.INTER_CUBIC)

# THRESHOLD CALIBRATION BARS AND ANSWERS
thresh1 = cv2.inRange(img, 0, 60)
thresh2 = cv2.inRange(img, 70, 200)

# FILL IN ANSWERS
mod = cv2.morphologyEx(thresh1, cv2.MORPH_OPEN, np.ones((2,2), np.uint8))
mod = cv2.morphologyEx(mod, cv2.MORPH_CLOSE, np.ones((7,7), np.uint8))

# FIND CALIBRATION BARS
contours = cv2.findContours(thresh2, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[1]
areas = []
for c in contours:
    areas.append(cv2.contourArea(c))
contours = sorted(zip(areas, contours), key=lambda x:x[0], reverse=True)

top, bottom = (cv2.boundingRect(contours[0][1]), cv2.boundingRect(contours[1][1])) if cv2.boundingRect(contours[0][1])[1] \
               < cv2.boundingRect(contours[1][1])[1] else (cv2.boundingRect(contours[1][1]), cv2.boundingRect(contours[0][1]))

slope = math.atan((bottom[0]-top[0])/(bottom[1]-top[1]))
width = (top[2] + bottom[2])/2/math.cos(slope)
height = (bottom[1] - top[1])/math.cos(slope)

cont = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
# cont = cv2.rectangle(cont, (top[0], top[1]), (top[0]+top[2], top[1]+top[3]), (0,255,0))
# cont = cv2.rectangle(cont, (bottom[0], bottom[1]), (bottom[0]+bottom[2], bottom[1]+bottom[3]), (0,0,255))
cont = cv2.line(cont, (top[0], top[1]+(top[3] if slope>0 else 0)), (top[0]+int(math.cos(-slope)*width), top[1]+int(math.sin(-slope)*width)+(top[3] if slope>0 else 0)), (255,0,0), 2)
cont = cv2.line(cont, (top[0], top[1]+(top[3] if slope>0 else 0)), (int(top[0]+math.sin(slope)*height), int(top[1]+math.cos(slope)*height)+(bottom[3] if slope>0 else 0)), (255,0,0),2)

# READ ANSWERS
values = [[0 for x in range(13)] for y in range(18)]
positions = []
for y in range(18):
    tmp = []
    for x in range(13):
        drawdot(x, y, cont, True)

# SHOW IMAGE, WAIT FOR CORRECTIONS
cv2.imshow('img', cont)
cv2.setMouseCallback('img', click)
try:
    if cv2.waitKey() not in [13, 32]: # SPACE OR ENTER
        sys.exit()
except ValueError:
    sys.exit()

# READ TEAM, MATCH NUMBER
team = sum(2**i for i, v in enumerate(values[0]) if v)
match = sum(2**i for i, v in enumerate(values[1]) if v)
print("Team: " + str(team))
print("Match: " + str(match))

# READ CONFIGURATION DATA
config = configparser.ConfigParser()
config.read("config.ini")

# WRITE TO DATA FILE
exists = Path(str(team) + ".csv").is_file()
with open(str(team) + ".csv", "a+") as file:
    if not exists:
        file.write(str(team) + "\nMatch,")
        for i, name in dict(config.items("names")).items():
            file.write(name + ",")
        file.write("\n")
    file.write(str(match) + ",")
    for i, value in enumerate(values[2:], start=1):
        if config["types"][str(i)] == "Single":
            file.write(single(value))
        elif config["types"][str(i)] == "Binary":
            file.write(binary(value))
        elif config["types"][str(i)] == "TF":
            file.write(tf(value))
        elif config["types"][str(i)] == "Multiple":
            file.write(multiple(value))
    file.write("\n")