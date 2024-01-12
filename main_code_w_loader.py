# -*- coding: utf-8 -*-
"""
pyQt5 application for capturing and displaying lidara data

====================================================
  1) Create camera object and set initial parameters
  2) Start Timer at 100 milliseconds
  3) Every 10 clicks of timer(1 second)
         get zed camera position and orientation
         get hz lidar data
         get vt lidar data
         diaply data on 2d and 3d plots
"""
import sys
import os
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget,  QMainWindow
from PyQt5.QtWidgets import QDirModel
#from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPixmap,  QPainter, QColor, QFont
from PyQt5.QtCore import QTimer,QDateTime

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
from mpl_toolkits.mplot3d import axes3d


#from mainwindow import Ui_MainWindow

import datetime
import time
from stat import S_ISREG, ST_CTIME, ST_MODE
import locale
import sqlite3
import math
import serial

import re

import pyzed.sl as sl

import utils


global mainPath
mainPath = 'C:/MyCode/dual_lidar_3d'


global articles
articles = ['a', 'an', 'of', 'the', 'is']

#========================================

global curLogRow
curLogRow = -1

global curLogDepth
curLogDepth = 0

global objName
objName = ""



# ===========================================================
# ============================================================

#=============================
#// define canvas for lidar point plot
class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


#=============================
#// define canvas for lidar point 3d plot
class Mpl3dCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111, projection='3d')
        super(Mpl3dCanvas, self).__init__(fig)

        self.axes.mouse_init()

# ===========================================================

class MyApp(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        uic.loadUi("mainwindow.ui", self)
        
        self.setupUi(self)

      
        #// set values for test runs
        self.curProjIdc = "Test Project"
        self.curSiteIdc = "Test Site"
        self.curSubSiteIdc = "Test SubSite"
        self.curLevelIdc = "Test Level"
        self.curCollAreaIdc = "Test CollArea"
        
        self.collOperator = "Test Operator"
        self.collDrone = "Evo2"
                
        self.collIdc = ""
        self.collId = 0
        self.ldrImg = ""


        self.timer=QTimer()
        self.timerCnt = 0
        self.curInterval = 250

        #// set initial variables
        self.vtPlane = 0.0
        self.curDir = 0.0
        self.curDeg = 0.0
        self.curRad = 0.0
        self.imuDeg = 0.0

        self.appPath = os.path.dirname(os.path.realpath(__file__))

        self.dirImg = QPixmap()

        self.capCnt = 0

        self.zedX = 0.0
        self.zedY = 0.0
        self.zedZ = 120.0
        self.zedDir = 0.0
        self.toCeil = 0.0
        self.toFloor = 0.0
        self.fwdDist = 0.0
        self.bkwdDist = 0.0
        self.leftDist = 0.0
        self.rghtDist = 0.0
        self.lastDir = 0.0
        
        self.vertexCnt = 0
        self.plyRecs = []
        
        self.r1 = 0.0
        self.r2 = 0.0
        self.r3 = 0.0
        
        self.ldrCapCnt = 0

        self.hzPort = "COM5"
        self.vtPort = "COM8"
        
        
        self.hasHZlidar = False
        self.hasVTlidar = False
        #// Horizontal variables
        if os.path.exists("/dev/ttyUSB0"):
            self.hasHZlidar = True
            
            self.serHz = serial.Serial(port="/dev/ttyUSB0",
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                )
        
            self.xcrdsHz = []
            self.ycrdsHz = []
            self.angsHz = []
            self.distsHz = []
            self.idxH0 = 0
            self.idxH90 = 0
            self.idxH180 = 0
            self.idxH270 = 0


        
        #// Vertical variables
        if os.path.exists("/dev/ttyUSB1"):
            self.hasVTlidar = True
            self.serVt = serial.Serial(port='/dev/ttyUSB1',
                baudrate=230400,
                timeout=5.0,
                bytesize=8,
                parity='N',
                stopbits=1) 
            
            self.xcrdsVt = []
            self.ycrdsVt = []
            self.zcrdsVt = []
            self.angsVt = []
            self.distsVt = []
            self.idxV0 = 0
            self.idxV90 = 0
            self.idxV180 = 0
            self.idxV270 = 0
        
        #// set camera defs
        self.zed = sl.Camera()
        self.camera_pose = sl.Pose()
        self.py_translation = sl.Translation()
        self.pose_data = sl.Transform()
        
        #// camera resolution
        #self.zedRes = "HD1080"
        self.zedRes = "HD2K"
        
        #// get userName from system
        usrName = os.environ.get('USERNAME')
        usrPwd = ""
        if usrName == "nvidia":
            usrPwd = "nvidia"
        if "acms" in usrName:
            usrPwd = "asc123"
        
        
        self.collPath = "/home/" + usrName + "/Desktop/AutoCMS/files/collections"
        self.logPath = "/home/" + usrName + "/Desktop/AutoCMS/files/logs"
        self.collFldr = ""
        self.upldPath = "/home/" + usrName + "/Desktop/AutoCMS/files/toUpload"
        self.svoFile = ""
        self.dbPath = "/home/" + usrName + "/Desktop/AutoCMS/db/acms.db" 
        
        print("self.dbPath: ", self.dbPath)
        
        
        #// define plots for all windows
        px = 1/100
        self.scHz2d = MplCanvas(self, width=378*px, height=348*px, dpi=100)
        self.scHz2d.setParent(self.ui.grp_hz2dPlot)
        self.scHz2d.setGeometry(2,2,378,348)
        #self.scHz2d.axes.invert_xaxis()
        #self.scHz2d.axes.invert_yaxis()
        self.scHz2d.axes.set_xlim([-500,500])
        self.scHz2d.axes.set_ylim([-500,500])

        self.scVt2d = MplCanvas(self, width=378*px, height=348*px, dpi=100)
        self.scVt2d.setParent(self.ui.grp_vt2dPlot)
        self.scVt2d.setGeometry(2,2,378,348)
        self.scVt2d.axes.set_xlim([-500,500])
        self.scVt2d.axes.set_ylim([-200,200])

        self.scDr2d = MplCanvas(self, width=378*px, height=348*px, dpi=100)
        self.scDr2d.setParent(self.ui.grp_drone_loc2dPlot)
        self.scDr2d.setGeometry(2,2,378,348)

        self.sc3d = Mpl3dCanvas(self, width=378*px, height=348*px, dpi=100)
        self.sc3d.setParent(self.ui.grp_3dPlot)
        self.sc3d.setGeometry(2,2,378,348)
        
        
        #// define styles to use on some widgets
        self.hdrstyle = "::section{Background-color:rgb(150, 150, 150);border-radius:14px;font-size:8pt; font-weight:600; color:#343961;}"
        self.lblstyle = "::section{Background-color:rgb(150, 150, 150);border-radius:14px;font-size:8pt; font-weight:600; color:#343961;}"

        #// lists for storing pose data
        self.zedEulerRad = []
        self.zedEulerAng = []
        self.zedQuats = []
        
        #// for storing imu pose
        self.imuPose = []
        
        logFile = self.logPath + "zedRotLog.txt"
        self.zedlog = open(logFile, 'w')
        
        #// run setup
        self.app_setup()

    #===============================================================================
    ####       signals and slots
    #===============================================================================
        self.ui.cbx_TimeMilliSecs.currentIndexChanged.connect(self.set_ldrInterval)
        self.ui.pbEndCapture.pressed.connect(self.end_lidar_capture)
        self.ui.pbStartCapture.pressed.connect(self.start_lidar_capture)
        self.ui.pbExit.pressed.connect(self.exit_app)
        self.ui.pbSavePtCloud.pressed.connect(self.save_to_pointcloud)


    #======================================================================
    ###  Set some initial values and options
    #======================================================================
    



    #==============================================================================
    ###       Function and Sub definitions
    #==============================================================================
 
    #===========================
    def  set_ldrInterval(self):
        self.curInterval = int(self.ui.cbx_TimeMilliSecs.currentText())
        self.timer.setInterval(self.curInterval)


    #===========================
    def  end_lidar_capture(self):
        self.serHz.close()
        if os.path.exists("/dev/ttyUBS1"):
            self.serVt.close()
        self.stop_timer()
        self.zed.close()
        
        self.zedlog.close()
        
        self.create_ply_file()

    #===========================
    def  start_lidar_capture(self):
        self.timer.setInterval(self.curInterval)
        self.set_ldrInterval()
        
        self.create_zed_camera_object()
        
        #// print camera settings
        curParams = self.zed.get_init_parameters()
        print("coordsys: ", curParams.coordinate_system)
        
        self.timer.timeout.connect(self.show_time)

        self.ldrCapCnt = 0
        
        self.start_timer()
        
        if self.debugMode == True:
            print("Get next collid")
        
        self.get_next_collid()
        
        
        if self.debugMode == True:
            print("write header to log file")
        #/ write header to zedlog
        zedHdr = "qauternion|yawDir|euler angle|euler radians\n"
        self.zedlog.write(zedHdr)
        

    #==========================
    def start_timer(self):  
        self.timer.start(self.curInterval)


    #===================
    def show_time(self):
        self.timerCnt = self.timerCnt + 1
        if self.debugMode == True:
            print("get_fast_zed_pose")
        self.get_fast_zed_pose()
        if self.timerCnt % 1 == 0:
            self.ldrCapCnt = self.ldrCapCnt + 1
            self.ui.txtVTcount.setText(str(self.ldrCapCnt))
            self.ui.txtVTcount.repaint()
            if self.debugMode == True:
                print("get_zed_pose_3")
            self.get_zed_pose_3()
            self.update_zed_pose()
            self.update_dir_image()
            if self.debugMode == True:
                print("get_hz_lidar_data")
            self.get_hz_lidar_data()

            if os.path.exists("/dev/ttyUSB1"):
                if self.debugMode == True:
                    print("get_vt_lidar_data")
                self.get_vt_lidar_data()
            else:
                self.angsVt = []
                self.distsVt = []
                
            if self.debugMode == True:
                print("write_lidar_record")
            self.write_lidar_record()
        

    #===========================
    def  save_to_pointcloud(self):
        self.curDir = 36.76
        self.update_dir_image()


    #==========================
    def stop_timer(self):
        self.timer.stop()
        

    #===========================
    def  exit_app(self):
        self.stop_timer()
        self.zed.close()
        self.close()

    #===========================
    def update_dir_image(self):
        self.dirImg = QPixmap(self.appPath + '/icons/up_blu_32.png')
        transform = QtGui.QTransform().rotate(0.0 - self.curDir)
        self.dirImg = self.dirImg.transformed(transform, QtCore.Qt.SmoothTransformation)
        self.ui.lblCurDir.setPixmap(self.dirImg)


    #===========================
    def app_setup(self):

        #== Add Depth Intervals
        self.ui.cbx_TimeMilliSecs.blockSignals(True)
        self.ui.cbx_TimeMilliSecs.addItem("100")
        self.ui.cbx_TimeMilliSecs.addItem("200")
        self.ui.cbx_TimeMilliSecs.addItem("300")
        self.ui.cbx_TimeMilliSecs.addItem("400")
        self.ui.cbx_TimeMilliSecs.addItem("500")
        self.ui.cbx_TimeMilliSecs.addItem("600")
        self.ui.cbx_TimeMilliSecs.addItem("750")
        self.ui.cbx_TimeMilliSecs.addItem("1000")
        self.ui.cbx_TimeMilliSecs.setCurrentIndex(4)
        self.ui.cbx_TimeMilliSecs.blockSignals(False)

        self.dirImg = QPixmap(self.appPath + '/icons/up_blu_32.png')
        self.ui.lblCurDir.setPixmap(self.dirImg)
      
        self.ui.label_8.setFont(QFont('Arial Bold', 11))
        self.ui.label_9.setFont(QFont('Arial Bold', 11))
        self.ui.label_10.setFont(QFont('Arial Bold', 11))
        self.ui.label_12.setFont(QFont('Arial Bold', 11))


    #===========================
    def get_vt_lidar_data(self):        
        self.serVt = serial.Serial(port='/dev/ttyUSB1',
            baudrate=230400,
            timeout=5.0,
            bytesize=8,
            parity='N',
            stopbits=1) 
            
        tmpString = ""
        anglesVt = list()
        distancesVt = list()

        vectorsVt = []
        myAngsVt = list()
        
        anglesVt.clear()
        distancesVt.clear()
        myAngsVt.clear()
        
        self.xcrdsVt = []
        self.ycrdsVt = []
        self.zcrdsVt = []
        self.angsVt = []
        self.distsVt = []
  
        i = 0
        ct = 0
        while ct < 120:
            ct = ct + 1
            loopFlag = True
            flag2c = False
        
            if(i == 39):
                #// write to vectors
                vx = -1
                for ag in anglesVt:
                    vx = vx + 1   
                    vec = [anglesVt[vx], distancesVt[vx]]
                    vectorsVt.append(vec)

                anglesVt.clear()
                distancesVt.clear()
                myAngsVt.clear()
                i = 0
                
            while loopFlag:
                b = self.serVt.read()
                tmpInt = int.from_bytes(b, 'big')
                
                if (tmpInt == 0x54):
                    tmpString +=  b.hex()+" "
                    flag2c = True
                    continue
                
                elif(tmpInt == 0x2c and flag2c):
                    tmpString += b.hex()
        
                    if(not len(tmpString[0:-5].replace(' ','')) == 90 ):
                        tmpString = ""
                        loopFlag = False
                        flag2c = False
                        continue
        
                    lidarData = utils.CalcLidarData(tmpString[0:-5])
                    
                    #// get anles in degrees
                    FSA = lidarData.FSA
                    LSA = lidarData.LSA
                    angInc = 0.00
                    angInc = abs(LSA - FSA) / 12
                    
                    for ag in range(0,12):
                        if FSA + angInc > 359.9:
                            curAng = 360 - (FSA + angInc)
                        else:
                            curAng = FSA + angInc 
                        
                    anglesVt.extend(lidarData.Angle_i)
                    myAngsVt.extend(lidarData.angDg_i)
                    distancesVt.extend(lidarData.Distance_i)
                    self.distsVt = distancesVt
                    self.angsVt = anglesVt
                        
                    tmpString = ""
                    loopFlag = False
                else:
                    tmpString += b.hex()+" "
                
                flag2c = False
            
            i +=1       
                 
        #// get x,y,z coords        
        cnt = 0
        vavs = []
        pi = 22 / 7
        for vc in vectorsVt:
            ##print(vc)
            if (vc[1] * 1) > 100:
                vavs.append(vc[0]*(180/pi))
                cnt = cnt + 1
                va = vc[0]
                vd = vc[1] * 1
                
                if vd > 100:
                    #// set x,y,z plane
                    self.vtPlane = self.curDir + 90.0
                    if self.vtPlane > 360.0:
                        self.vtPlane = self.vtPlane - 360.0
                    vtRad = math.radians(self.vtPlane)
                    vaR = math.radians(va)
                    #//calculate x,y,z using zed current x,y,z
                    vx = self.zedX + (vd * math.sin(va) * math.cos(self.vtPlane))
                    vy = self.zedY + (vd * math.sin(va) * math.sin(self.vtPlane))
                    vz = self.zedZ + (vd * math.cos(va))
                       
                    angRad = 0.785398
                    hyp = vd
                    opp = hyp * math.sin(angRad)
                    adj = hyp * math.cos(angRad)
                                  
                    self.angsVt.append(va)
                    self.distsVt.append(vd)
                    #self.vdists.append(opp)
                    self.xcrdsVt.append(vx)
                    self.ycrdsVt.append(vy)
                    self.zcrdsVt.append(vz)
                    
                    #// write x,y,y to .ply file
                    ptStr = str(vx) + " " + str(vy) + " " + str(vz)\
                        + " 0 0 240\n" 
                    self.plyRecs.append(ptStr)
                    self.vertexCnt = self.vertexCnt + 1
                                                  
        #self.idxV0 = vavs.index(self.closest(vavs, 0))
        ##self.idxV180 = vavs.index(self.closest(vavs, 180))
        
        #// populate up and down variables
        #self.dwnDist = str(self.xcrdsVt[self.idxV0])
        ##self.upDist = str(self.xcrdsVt[self.idxV180])
        ##self.zedZ = self.xcrdsVt[self.idxV0]
        
        ##self.ui.lbl_DistToFloor.setText(str(self.dwnDist))
        ##self.ui.lbl_DistToCeiling.setText(str(self.upDist))

        ##self.scVt2d.axes.set_xlim(-300, 300)
        ##self.scVt2d.axes.set_ylim(-300, 300)
          
        self.scVt2d.axes.scatter(self.xcrdsVt, self.ycrdsVt, c='b', marker=".")
        self.scVt2d.draw()
        
        
        #// desiplay vertical lidar data in 3d
        self.sc3d.axes.scatter(self.xcrdsVt, self.ycrdsVt, self.zcrdsVt, c='b', marker=".")
        self.sc3d.draw()


    #===========================
    def get_hz_lidar_data(self):
        self.serHz = serial.Serial(port='/dev/ttyUSB0',
            baudrate=230400,
            timeout=5.0,
            bytesize=8,
            parity='N',
            stopbits=1) 
        
        tmpString = ""
        linesHz = list()
        anglesHz = list()
        distancesHz = list()
        xcoordsHz = list()
        ycoordsHz = list()
        lnsegsHz = []
        vectorsHz = []
        myAngsHz = list()
        
        anglesHz.clear()
        distancesHz.clear()
        myAngsHz.clear()
        
        self.xcrdsHz = []
        self.ycrdsHz = []
        self.angsHz = []
        self.distsHz = []
  
        i = 0
        ct = 0
        while ct < 120:
            ct = ct + 1
            loopFlag = True
            flag2c = False
        
            if(i % 40 == 39):
                if('line' in locals()):
                    pass
                    #line.remove()
                #line = ax.scatter(angles, distances, c="pink", s=5)
                #// write to vectors
                vx = -1
                for ag in anglesHz:
                    vx = vx + 1   
                    vec = [anglesHz[vx], distancesHz[vx]]
                    vectorsHz.append(vec)

                anglesHz.clear()
                distancesHz.clear()
                myAngsHz.clear()
                i = 0
                
            while loopFlag:
                b = self.serHz.read()
                tmpInt = int.from_bytes(b, 'big')
                
                if (tmpInt == 0x54):
                    tmpString +=  b.hex()+" "
                    flag2c = True
                    continue
                
                elif(tmpInt == 0x2c and flag2c):
                    tmpString += b.hex()
        
                    if(not len(tmpString[0:-5].replace(' ','')) == 90 ):
                        tmpString = ""
                        loopFlag = False
                        flag2c = False
                        continue
        
                    lidarData = utils.CalcLidarData(tmpString[0:-5])
                    
                    #// get anles in degrees
                    FSA = lidarData.FSA
                    LSA = lidarData.LSA
                    angInc = 0.00
                    angInc = abs(LSA - FSA) / 12
                    
                    for ag in range(0,12):
                        if FSA + angInc > 359.9:
                            curAng = 360 - (FSA + angInc)
                        else:
                            curAng = FSA + angInc 
                        
                    anglesHz.extend(lidarData.Angle_i)
                    myAngsHz.extend(lidarData.angDg_i)
                    distancesHz.extend(lidarData.Distance_i)
                    self.distsHz = distancesHz
                    self.angsHz = anglesHz
                        
                    tmpString = ""
                    loopFlag = False
                else:
                    tmpString += b.hex()+" "
                
                flag2c = False
            
            i +=1
                 
        #// get x,y coords        
        cnt = 0
        vavs = []
        pi = 22 / 7
        for vc in vectorsHz:
            ##print(vc)
            if (vc[1] * 1) > 150:
                vavs.append(vc[0]*(180/pi))
                cnt = cnt + 1
                va = vc[0]
                vd = vc[1] * 1
                x = (vd * math.cos(va)) * 1
                y = (vd * math.sin(va)) * 1
                
                angRad = 0.785398
                hyp = vd
                opp = hyp * math.sin(angRad)
                adj = hyp * math.cos(angRad)
                              
                self.angsHz.append(va)
                self.distsHz.append(vd)
                ##self.distsHz.append(adj)
                self.xcrdsHz.append(x)
                self.ycrdsHz.append(y)
                
        #// get cardinal distances
        self.idxH0 = vavs.index(self.closest(vavs, 0))
        self.idxH90 = vavs.index(self.closest(vavs, 90))
        self.idxH180 = vavs.index(self.closest(vavs, 180))
        self.idxH270 = vavs.index(self.closest(vavs, 270))
        
        #// populate fwd and bkwd variables
        self.fwdXY = str(self.xcrdsHz[self.idxH0]) + "," + str(self.ycrdsHz[self.idxH0])
        self.bkwdXY = str(self.xcrdsHz[self.idxH180]) + "," + str(self.ycrdsHz[self.idxH180])
        
        #// show distances inlist
        
        self.ui.lstDistances.clear()
        self.ui.lstDistances.addItem(" Fwd: " + str(vectorsHz[self.idxH0][1]) + " cm" )
        self.ui.lstDistances.addItem(" Bck: " + str(vectorsHz[self.idxH180][1]) + " cm" )
        self.ui.lstDistances.addItem(" Lft: " + str(vectorsHz[self.idxH270][1]) + " cm" )
        self.ui.lstDistances.addItem("Rght: " + str(vectorsHz[self.idxH90][1]) + " cm" )
             
        self.ui.lstDistances.repaint()
        
        ##self.scHz2d.axes.set_xticks([])
        ##self.scHz2d.axes.set_yticks([])
        if self.timerCnt == 1:
            self.scHz2d.axes.scatter(self.ycrdsHz, self.xcrdsHz, marker=".")
            self.scHz2d.show()
            self.scHz2d.draw() 


    #============================
    def update_zed_pose(self):

        print("self.curRad: ", self.curRad,"self.curDir: ", self.curDir,"self.vtPlane: ", self.vtPlane)
        print("========")        



    #=============================
    def get_zed_pose_log(self):
        #// write file of zed euler angles and quaternion values for 0 to 360
        runtime = sl.RuntimeParameters()
        if self.zed.grab(runtime) == sl.ERROR_CODE.SUCCESS:
            self.camera_pose = sl.Pose()
            tracking_state = self.zed.get_position(self.camera_pose, sl.REFERENCE_FRAME.WORLD)
            if tracking_state == sl.POSITIONAL_TRACKING_STATE.OK:
                rotation = self.camera_pose.get_euler_angles(radian=True)
                translation = self.camera_pose.get_translation(self.py_translation)
                self.pose_data = self.camera_pose.pose_data(sl.Transform())
                
                ##rotV = pose_data.get_rotation_vector()
                ##rotM = pose_data.get_rotation_matrix()
                
                #self.zedX = round((translation.get()[0] * 1), 2)
                #self.zedY = round((translation.get()[1] * 1), 2)
                #self.zedZ = str(rotation).replace("[","").replace("]","").strip()
                #// get 3d rotations
                self.r1 = round(rotation[0],2)
                self.r2 = round(rotation[1],2)
                self.r3 = round(rotation[2],2)
                
         
                per = self.camera_pose.get_euler_angles(radian=True)
                pea = self.camera_pose.get_euler_angles(radian=False)        
                
                ##py_orientation = sl.Orientation()
                q0 = round(self.camera_pose.get_orientation().get()[3], 3)
                q1 = round(self.camera_pose.get_orientation().get()[0], 3)
                q2 = round(self.camera_pose.get_orientation().get()[1], 3)
                q3 = round(self.camera_pose.get_orientation().get()[2], 3)
                pq = str(q0) + "," + str(q1) + "," + str(q2) + "," + str(q3)
                
                self.curRad = math.atan2(2 * (q0 * q3 + q1 * q2), 1-2 * (q2**2 + q3**2))
                self.curDeg = math.degrees(self.curRad)
                
                if self.curDeg < 0.0:
                    self.curDir = 360.0 + self.curDeg
                else:
                    self.curDir = self.curDeg
                    
                
                
                self.pose_data = self.camera_pose.pose_data(sl.Transform())
                
                logStr = str(pq) + "|" + str(self.curDir) + "|" + str(pea) + "|" + str(per) + "\n"
                
                self.zedlog.write(logStr)
                
        


    #=============================
    def get_fast_zed_pose(self):
        runtime = sl.RuntimeParameters()
        if self.zed.grab(runtime) == sl.ERROR_CODE.SUCCESS:
            tracking_state = self.zed.get_position(self.camera_pose)
            if tracking_state == sl.POSITIONAL_TRACKING_STATE.OK:
                rotation = self.camera_pose.get_euler_angles(radian=True)
                translation = self.camera_pose.get_translation(self.py_translation)
                self.pose_data = self.camera_pose.pose_data(sl.Transform())
                
                ##rotV = pose_data.get_rotation_vector()
                ##rotM = pose_data.get_rotation_matrix()
                
                ##self.zedX = round((translation.get()[0] * 1), 2)
                ##self.zedY = round((translation.get()[1] * 1), 2)
                self.zedDir = str(rotation).replace("[","").replace("]","").strip()
                #// get 3d rotations
                self.r1 = round(rotation[0],2)
                self.r2 = round(rotation[1],2)
                self.r3 = round(rotation[2],2)
                
                #// adjust dir for radians gt then 1.0
                if self.r3 >= 3.0:
                    adjRad = self.r3 - 3.0
                    self.curDir = math.degrees(float(adjRad)) + 270.0
                elif self.r3 >= 2.0:
                    adjRad = self.r3 - 2.0
                    self.curDir = math.degrees(float(adjRad)) + 180.0
                elif self.r3 >= 1.0:
                    adjRad = self.r3 - 1.0
                    self.curDir = math.degrees(float(adjRad)) + 90.0
                else:
                    adjRad = self.r3
                    self.curDir = math.degrees(float(adjRad))
            

    #=============================
    def get_zed_pose_3(self):
        runtime = sl.RuntimeParameters()
        
        sensors_data = sl.SensorsData()
     
        ##sensors_data = sl.SensorsData()
        
        self.imu_or = ""
        self.imu_acc = ""
        self.imu_av = ""
        self.mag_fld = 0.0
        self.bar_ap = ""
        
        #=============================================================
   
        ##if self.zed.grab(runtime) == sl.ERROR_CODE.SUCCESS:
        tracking_state = self.zed.get_position(self.camera_pose)
        if tracking_state == sl.POSITIONAL_TRACKING_STATE.OK:
            ##rotation = self.camera_pose.get_euler_angles(radian=True)
            translation = self.camera_pose.get_translation(self.py_translation)
            self.pose_data = self.camera_pose.pose_data(sl.Transform())
            
            #// get imu pose
            self.zed.get_sensors_data(sensors_data, sl.TIME_REFERENCE.CURRENT)
            imuQuat = sensors_data.get_imu_data().get_pose().get_orientation().get()
            camQuat = self.camera_pose.get_orientation().get()
            
            #// Disply the orientation euler angles
            eulerRot = self.camera_pose.get_euler_angles(radian=True)
            pose_data = self.camera_pose.pose_data(sl.Transform())
            
            self.rot1 = round(eulerRot[0],2)
            self.rot2 = round(eulerRot[1],2)
            self.rot3 = round(eulerRot[2],2)   
            
            camDir = math.degrees(float(self.rot3))
                      
            ##rotV = pose_data.get_rotation_vector()
            ##rotM = pose_data.get_rotation_matrix()
            
            ##self.zedX = round((translation.get()[0] * 1), 2)
            ##self.zedY = round((translation.get()[1] * 1), 2)
            
            q0 = round(self.camera_pose.get_orientation().get()[3], 3)
            q1 = round(self.camera_pose.get_orientation().get()[0], 3)
            q2 = round(self.camera_pose.get_orientation().get()[1], 3)
            q3 = round(self.camera_pose.get_orientation().get()[2], 3)
            
            self.curRad = math.atan2(2 * (q0 * q3 + q1 * q2), 1-2 * (q2**2 + q3**2))
            self.curDeg = math.degrees(self.curRad)
            
            #// calc imu dir
            iq0 = round(imuQuat[3], 3)
            iq1 = round(imuQuat[0], 3)
            iq2 = round(imuQuat[1], 3)
            iq3 = round(imuQuat[2], 3)  
            imuRad = math.atan2(2 * (iq0 * iq3 + iq1 * iq2), 1-2 * (iq2**2 + iq3**2))
            self.imuDeg = math.degrees(imuRad)
            
            if self.imuDeg < 0.0:
                self.curDir = 360.0 + self.imuDeg
            else:
                self.curDir = self.imuDeg
                
                
                
            print("self.curDeg: ", self.curDeg)
            print("self.curDir: ", self.curDir)
            print("====")
            print("camDir: ", camDir)
            print("imuDir: ", self.imuDeg)


    #=============================
    def get_zed_pose_2(self):
        
        tracking_state = self.zed.get_position(self.camera_pose)
        if tracking_state == sl.POSITIONAL_TRACKING_STATE.OK:
            rotation = self.camera_pose.get_euler_angles(radian=False)
            translation = self.camera_pose.get_translation(self.py_translation)
            pose_data = self.camera_pose.pose_data(sl.Transform())
            
            rotV = pose_data.get_rotation_vector()
            rotM = pose_data.get_rotation_matrix()
            
            ##self.zedX = round((translation.get()[0] * 1), 2)
            ##self.zedY = round((translation.get()[1] * 1), 2)
            self.zedDir = str(rotation).replace("[","").replace("]","").strip()
            #// get 3d rotations
            self.rot1 = round(rotation[0],2)
            self.rot2 = round(rotation[1],2)
            self.rot3 = round(rotation[2],2)
            
            ##print("3d Quats: ", str(self.r1),str(self.r2),str(self.r3))
            print("rotV:", rotV)
            print("rotM:", rotM)
                                          
            zrot = ' '.join(str(self.zedDir).split())
            
            #print(zrot.split(' ')[2])
            self.curDir = math.degrees(float(zrot.split(' ')[2]))
            print("curDir:", self.curDir)


    #===========================
    def get_zed_pose_quat(self):
        self.camera_pose = sl.Pose()
        py_translation = sl.Translation()
        pose_data = sl.Transform()
        
        self.zed.get_position(self.camera_pose, sl.REFERENCE_FRAME.WORLD)
        
        # Display the translation and timestamp
        py_translation = sl.Translation()
        ##self.zedX = round(self.camera_pose.get_translation(py_translation).get()[0], 3)
        ##self.zedY = round(self.camera_pose.get_translation(py_translation).get()[1], 3)
        ##self.zedZ = round(self.camera_pose.get_translation(py_translation).get()[2], 3)
        print("Translation: Tx: {0}, Ty: {1}, Tz {2}, Timestamp: {3}\n".format(self.zedX, self.zedY, self.zedZ, self.camera_pose.timestamp.get_milliseconds()))
        
        # Display the orientation quaternion
        py_orientation = sl.Orientation()
        ox = round(self.camera_pose.get_orientation(py_orientation).get()[1], 3)
        oy = round(self.camera_pose.get_orientation(py_orientation).get()[2], 3)
        oz = round(self.camera_pose.get_orientation(py_orientation).get()[3], 3)
        ow = round(self.camera_pose.get_orientation(py_orientation).get()[0], 3)
        print("Orientation: Ox: {0}, Oy: {1}, Oz {2}, Ow: {3}\n".format(ox, oy, oz, ow))
        
        #// Disply the orientation euler angles
        eulerRot = self.camera_pose.get_euler_angles(radian=True)
        pose_data = self.camera_pose.pose_data(sl.Transform())
        rotV = pose_data.get_rotation_vector()
        rotM = pose_data.get_rotation_matrix()
        
        self.rot1 = round(eulerRot[0],2)
        self.rot2 = round(eulerRot[1],2)
        self.rot3 = round(eulerRot[2],2)   
        
        self.curDir = math.degrees(float(self.rot3))
        
        print("rotV:", rotV)
        print("rotM:", rotM)
        print("rot3:", self.rot3)
        print("zedDir:", self.zedDir)
        print("========")

    #===========================
    def set_zed_direction(self):
        pass


    #===========================
    def create_zed_camera_object(self):

        # Set configuration parameters
        init_params = sl.InitParameters()
        if self.zedRes == "HD1080":
            init_params.camera_resolution = sl.RESOLUTION.HD1080
        if self.zedRes == "HD2K":
            init_params.camera_resolution = sl.RESOLUTION.HD2K
        
        init_params.coordinate_units = sl.UNIT.CENTIMETER
        #init_params.coordinate_system = sl.COORDINATE_SYSTEM.IMAGE
        #init_params.coordinate_system = sl.COORDINATE_SYSTEM.LEFT_HANDED_Y_UP
        #init_params.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP
        #init_params.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Z_UP
        #init_params.coordinate_system = sl.COORDINATE_SYSTEM.LEFT_HANDED_Z_UP
        init_params.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Z_UP_X_FWD
        
        # No depth computation required here
        #init_params.depth_mode = sl.DEPTH_MODE.MEDIUM
        
        # Open the camera
        err = self.zed.open(init_params)
        if err != sl.ERROR_CODE.SUCCESS :
            print(repr(err))
            self.zed.close()
            exit(1)
            
        self.zedId = self.zed.get_camera_information().serial_number
        self.zedModel = self.zed.get_camera_information().camera_model
        print(self.zedModel, self.zedId)
            
        runtime = sl.RuntimeParameters()
        #runtime.sensing_mode = sl.SENSING_MODE.STANDARD
        
        tracking_params = sl.PositionalTrackingParameters()
        tracking_params.enable_pose_smoothing = True
        
        self.zed.enable_positional_tracking(tracking_params)
        
        self.zc = self.zed
        
        #// set initial pose
        self.camera_pose = sl.Pose()



    #========================================
    def get_zed_collarea_mesh(self):
        pass
    



    #// determine lidar record closest to given angle
    #=========================
    def closest(self, lst, K):
        return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))]
    
    
    #//===============================
    def write_collection_record(self):
        #// write collection record to db
        con = sqlite3.connect(self.dbPath)
        cur = con.cursor() 
        
        curTime = datetime.datetime.now()
        collDate = str(curTime)[0:10]
        collTime = str(curTime)[11:]
        
        collSql = "insert into collection values("\
            + "'" + self.curProjIdc + "',"\
            + "'" + self.curSiteIdc + "',"\
            + "'" + self.curSubSiteIdc + "',"\
            + "'" + self.curLevelIdc + "',"\
            + "'" + self.curCollAreaIdc + "',"\
            + str(self.collId) + ","\
            + str(self.collTypeId) + ","\
            + "'" + str(collDate) + "',"\
            + "'" + self.collOperator + "',"\
            + "'" + self.collDrone + "',"\
            + "'" + str(self.zedModel) + "',"\
            + "'" + str(collTime) + "',"\
            + "'Complete')"
        
        cur.execute(collSql)    
        
        con.commit()
        
    
    #//===============================
    def write_lidar_record(self):
        con = sqlite3.connect(self.dbPath)
        cur = con.cursor() 
        
        curTime = datetime.datetime.now()
        
        insSql = "insert into lidar_data values("\
            + "'" + self.curProjIdc + "',"\
            + "'" + self.curSiteIdc + "',"\
            + "'" + self.curSubSiteIdc + "',"\
            + "'" + self.curLevelIdc + "',"\
            + "'" + self.curCollAreaIdc + "',"\
            + str(self.collId) + ","\
            + str(self.ldrCapCnt) + ","\
            + "'" + str(curTime) + "',"\
            + "'" + str(self.angsHz) + "',"\
            + "'" + str(self.distsHz) + "',"\
            + "'" + str(self.angsVt) + "',"\
            + "'" + str(self.distsVt) + "',"\
            + str(self.zedX) + ","\
            + str(self.zedY) + ","\
            + str(self.zedZ) + ","\
            + "'" + self.fwdXY + "',"\
            + "'" + self.bkwdXY + "',"\
            + "'" + self.imu_or + "',"\
            + "'" + self.imu_acc + "',"\
            + "'" + self.imu_av + "',"\
            + "'" + self.ldrImg + "',"\
            + str(self.imuDeg) + ","\
            + "0.0,"\
            + str(self.toFloor) + ","\
            + str(self.toCeil) + ")"
        
        cur.execute(insSql)
        
        con.commit()
        
        con.close()


    #==========================
    def get_next_collid(self):
        
        con = sqlite3.connect(self.dbPath)
        cur = con.cursor() 
        
        #// get max collid
        cidSql = "select max(coll_id) from lidar_data"
        
        cur.execute(cidSql)
        res = cur.fetchone()
        #print(res[0])
        self.collId = res[0] + 1
        
        self.collIdc = "Collection_" + str(self.collId)
        
        self.collFldr = self.collPath + "/" + self.collIdc
        
        if os.path.exists(self.collFldr) == False:
            os.mkdir(self.collFldr)


    #===============================
    #// create .ply and write header
    def create_ply_file(self):
        plyFileName = self.collFldr + "/" + self.collIdc + ".ply" 
        
        print(plyFileName)
        
        plyFile = open(plyFileName, 'w')
        hdrRecs = "ply\n"\
        + "format ascii 1.0\n"\
        + "element vertex " + str(self.vertexCnt) + "\n"\
        + "property float x\n"\
        + "property float y\n"\
        + "property float z\n"\
        + "property uint8 red\n"\
        + "property uint8 green\n"\
        + "property uint8 blue\n"\
        + "end_header\n"
        
        plyFile.write(hdrRecs)
        
        #// add data to plyfile
        for rec in self.plyRecs:
            plyFile.write(rec)
            
        plyFile.close()
    
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())



