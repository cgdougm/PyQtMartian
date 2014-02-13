#!/bin/env python

"""
"""

import sys, os
import math
import glob
from collections import defaultdict

from PyQt4.QtOpenGL import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from random import uniform, randint
from odict import OrderedDict as odict

appPath = os.path.dirname( os.path.abspath(__file__) )
resourceDir = os.path.join( appPath, "resources")

currentDir  = os.getcwd()

iconPath = os.path.join(resourceDir, "icons")
fontDir  = os.path.join(resourceDir, "fonts")

defaultFontPath = os.path.join(fontDir, "arial.ttf")


try:
    from OpenGL import GL
except ImportError:
    app = QApplication(sys.argv)
    QMessageBox.critical(None, "OpenGL hellogl",
                            "PyOpenGL must be installed to run this example.",
                            QMessageBox.Ok | QMessageBox.Default,
                            QMessageBox.NoButton)
    sys.exit(1)

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from   pyglet.gl import *
import pyglet.font

import glFreeType

def vec(*args):
    return (GLfloat * len(args))(*args)
vec3 = vec
vec2 = vec
vec4 = vec


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Plastique')

availableFontFiles = glob.glob( os.path.join(fontDir, "*.*tf"))
availableFontPath = dict( [(k, os.path.join(fontDir, k)) for k in availableFontFiles ] )

BLACK = (0,0,0,1)
WHITE = (1,1,1,1)


# --- WIDGETS ---

class FloatSlider(QSlider):
    """
    QSlider with float range and log option
    """
    def __init__(self,parent=None):
        super(FloatSlider,self).__init__(parent)
        self.setRange(0,1000)
        self.setOrientation(Qt.Horizontal)
    def setFloatRange(self,lo,hi,log=False):
        self.loFloat = lo
        self.hiFloat = hi
        self.log     = log
    def setFloatValue(self,floatValue):
        self.setValue(self.fToI(floatValue))
    def iToF(self,intValue):
        return self.loFloat + (self.hiFloat-self.loFloat) * pow(float(intValue) / 1000.0, 2.2 if self.log else 1.0)
    def fToI(self,floatValue):
        nF = pow( (floatValue - self.loFloat) / (self.hiFloat-self.loFloat), 1.0/2.2 if self.log else 1.0)
        i = max(0,min(1000,int(nF*1000.0)))
        return i
    def wheelEvent(self, event):
        self.setValue(self.value() + event.delta()/abs(event.delta()) )
        event.accept()


# --- OBJECTS ---

class GraphicsObject(QObject):
    """
    Parametric geometry with display list
    """
    def __init__(self):
        self.color  = (1,1,1,1)
        self.glList = glGenLists(1)
        self._params = odict()
        self.shader = None
    def draw(self,frameNumber):
        glColor4f(*self.color)
        glCallList(self.glList)
    def addParam(self,param):
        self._params[param.name] = param
        return param
    def getParamValue(self,paramName,defaultValue=None):
        p = self._params.get(paramName,defaultValue)
        return p.value
    def updateParamValue(self,paramName,value):
        # Do not set the param, this is called by the param!
        self.rebuildList()
    def params(self):
        for p in self._params.values():
            yield p
    def setParamValue(self,paramName,value):
        p = self._params.get(paramName,None)
        if p == None: raise KeyError, paramName
        p.set(value)
    def rebuildList(self):
        pass
    def __str__(self):
        s = ["%s='%s'" % (p.name,p.value) for p in self.params()]
        ps = ", ".join(s)
        return "%s(%s)" % (self.__class__.__name__,ps)

class CircleObject(GraphicsObject):

    def __init__(self,radius=2.0,linewidth=2,npoints=100,angle=0.0,frameOffset=0):
        super(CircleObject,self).__init__()
        self.addParam(   FloatParameter("Radius",       self, initValue=1.0, minValue=0.0,  maxValue=5.0) )
        self.addParam(   FloatParameter("Radar gain",   self, initValue=0.0, minValue=0.0,  maxValue=1.0) )
        self.addParam(   FloatParameter("Radar angle",  self, initValue=0.0, minValue=0.0,  maxValue=360.0) )
        self.addParam( IntegerParameter("Num points",   self, initValue=100, minValue=3,    maxValue=500, step=1, geometry=True) )
        self.addParam( IntegerParameter("Line width",   self, initValue=1,   minValue=1,    maxValue=10,  step=1) )
        self.addParam( IntegerParameter("Frame offset", self, initValue=0,   minValue=-120, maxValue=120, step=1) )
        self.addParam(  ChoiceParameter("Font",         self,   choices=availableFontPath.keys()))
        self.rebuildList()
        
    def rebuildList(self):
        glNewList(self.glList, GL_COMPILE)
        glBegin(GL_LINE_LOOP)
        npts = self.getParamValue("Num points")
        for i in range(npts):
            theta = math.pi * 2.0 * float(i) / npts
            x = math.cos(theta)
            y = math.sin(theta)
            glVertex3d(x, y, 0.0)
        glEnd()
        glEndList()

    def draw(self,frameNumber):
        speed = 0.25
        seconds = float(frameNumber - self.getParamValue("Frame offset")) / 24.0
        rx = seconds * 360.0 * 0.2 * speed
        ry = seconds * 360.0 * 0.1 * speed
        rz = seconds * 360.0 * 0.0 * speed
        glRotatef(rz,0,0,1)
        glRotatef(ry,0,1,0)
        glRotatef(rx,1,0,0)
        glColor4f(*self.color)
        glLineWidth(self.getParamValue("Line width"))
        radius = self.getParamValue("Radius")
        glScalef(radius,radius,radius)
        glCallList(self.glList)

    def drawLine(self):
        glColor4f(*self.color)
        glLineWidth(self.linewidth)
        glBegin(GL_LINE_STRIP)
        for i in range(npts):
            x = size * ( -1.0 + 2.0 * float(i) / float(npts) ) * self.aspect
            y = amp * self.noiseTable[(i+int(speed*(self.frameOffset+frameNumber))) % len(self.noiseTable)]
            glVertex3d(x, y, 0.0)
        glEnd()

    def drawText(self,fontName="arial",size=72):
        self.string = "The quick brown fox jumped over the lazy dog's back"
        fontPath = availableFontPath.get(fontName,defaultFontPath)
        self.font = glFreeType.font_data(fontPath, size)
        speed = self.getParam("speed",1.0)
        amp   = self.getParam("amplitude",1.0)
        size  = 0.01*self.getParam("size",1.0)
        posX  = self.getParam("posX",0.0)
        posY  = self.getParam("posY",0.0)
        glPushMatrix()
        glTranslatef(posX,posY,0.0)
        glScalef(size,size,size)
        glColor4f(*self.color)
        self.font.glRender(self.string)
        glPopMatrix()


# --- MAIN DRAWING WIDGET ---

class GraphicsWidget(QGLWidget):

    def __init__(self,parent,main=None):
        QGLWidget.__init__(self,parent)
        self.main = main
        self.z = 5.0
        self.rx = 0.0
        self.ry = 0.0
        self.rz = 0.0
        self.objects = dict()
        self.shaders = dict()
        self.shader = None
        self.textObject = None
        self.fontChoice = "arial"
        self.angle = 0.0

        self.fg = WHITE
        self.bg = BLACK

        self.phosphorEffect = False
        self.phosphorBlend  = 0.25
        self.frameNumber    = 0
        self.frameOffset    = 0
        self.playbackState  = 'stop'
        self.numFrames      = 1
        self.baseName       = "output"
        self.lineWidth      = 1

        self.timer = QTimer(self)
        self.connect(self.timer, SIGNAL("timeout()"), self.timerCB)

        self.setFocusPolicy(Qt.WheelFocus)
        
    def wheelEvent(self,event):
        self.frameNumber += event.delta() // 120
        if self.frameNumber < 0:    self.frameNumber = 0
        if self.frameNumber > 9999: self.frameNumber = 9999
        self.update()

    def keyPressEvent(self,event):
        if event.key() == Qt.Key_Space:
            self.timelineCB("toggle")

    def setPhosphor(self,onOff):
        self.phosphorEffect = onOff

    def sizeHint(self):
        return QSize(1600, 800)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        #glClearColor(0.3, 0.3, 0.3, 1)
        #glEnable(GL_DEPTH_TEST)
        #glEnable(GL_CULL_FACE)
        #glEnable(GL_TEXTURE_2D)
        glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        #glBlendFunc(GL_SRC_ALPHA,GL_DST_ALPHA)
        glEnable(GL_BLEND)
        glHint(GL_POLYGON_SMOOTH_HINT,GL_NICEST)
        glEnable(GL_LINE_SMOOTH)

    def resizeGL(self,w,h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60., w / float(h), .1, 10000.)
        glMatrixMode(GL_MODELVIEW)

    def addObject(self,gObject):
        self.objects[gObject.name] = gObject
    
    def paramChangedCB(self,gObject,param):
        if param.geometry:
            gObject.rebuildList()
        self.updateGL()

    def paintGL(self):
        r, g, b, _ = self.bg
        glLoadIdentity()
        if self.phosphorEffect:
            glPushMatrix()
            glTranslatef(0, 0, -0.1)
            glColor4f(r, g, b, self.phosphorBlend)
            glBegin(GL_QUADS)
            glVertex3d(-2.0, -2.0, 0.0)
            glVertex3d(-2.0,  2.0, 0.0)
            glVertex3d( 2.0,  2.0, 0.0)
            glVertex3d( 2.0, -2.0, 0.0)
            glEnd()
            glPopMatrix()
        else:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glTranslatef(0, 0, -1.0 * self.z)
        for gObject in self.objects.values():
            gObject.draw(self.frameNumber)

    def update(self):
        if self.playbackState == "stop":
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.updateGL()
        self.emit(SIGNAL("updateFrame(int)"),self.frameNumber)

    def updateGui(self,paramObjName):
        gObject = self.objects[paramObjName] 
        if gObject.geometry:
            gObject.rebuildList()
        self.update()

    def timelineCB(self,mode):
        if mode == "rewind":
            self.playbackState  = 'stop'
            self.frameNumber = 0
            self.main.playButton.setChecked(False)
            self.update()
        elif mode == "stop":
            self.playbackState  = 'stop'
            self.timer.stop()
            self.frameNumber = 0
            self.main.playButton.setChecked(False)
            self.update()
        elif mode == "play":
            self.playbackState  = 'play'
            self.timer.start(1000 // 24)
        elif mode == "pause":
            self.playbackState  = 'pause'
            self.timer.stop()
        elif mode == "record":
            self.playbackState  = 'stop'
            self.timer.stop()
            self.frameNumber = 0
            self.update()
            self.recordSequence()
        elif mode == "toggle":
            if self.playbackState in ("pause", "stop"):
                self.timelineCB("play")
            else:
                self.timelineCB("pause")

    def recordSequence(self):
        outputPath = currentDir / "output"
        if not outputPath.exists():
            outputPath.mkdir()
        for frm in range(self.numFrames):
            frmPath = outputPath / ("%s.%04d.tif" % (self.baseName,frm))
            self.frameNumber = frm
            self.update()
            savePixmap = QPixmap.grabWindow(self.winId())
            savePixmap.save(frmPath)
        self.frameNumber = 0
        self.update()

    def timerCB(self):
        self.frameNumber += 1
        if self.frameNumber > 9999:
            self.frameNumber = 0
        self.update()

    def setResolution(self,opt):
        aspect = float(self.size().width()) / self.size().height()
        h = {"480p": 480, "720p": 720, "1080p": 1080}.get(opt,480)
        self.setFixedSize(QSize(int(aspect*h),h))

    def setAspect(self,opt):
        h = self.size().height()
        aspect = {"1:1": 1.0, "4:3": 4.0/3.0, "16:9": 16.0/9.0}.get(opt,1.0)
        w = int(aspect*h)
        self.setFixedSize(QSize(w,h))

    def setColor(self,opt):
        if opt == "B/W":
            self.fg, self.bg = (0,0,0,1), (1,1,1,1)
        elif opt == "W/B":
            self.bg, self.fg = (0,0,0,1), (1,1,1,1)
        elif opt == "Blue":
            self.bg, self.fg = (0,0,0.2,1), (0.3,0.6,1,1)
        glClearColor(*self.bg)
        for gObject in self.objects.values():
            gObject.color = self.fg
        self.update()

    def setNumFrames(self,num):
        self.numFrames = num

    def setFrameOffset(self,num):
        self.frameOffset = num
        self.update()

    def setLineWidth(self,n):
        self.lineWidth = n
        self.makeObjects()
        self.update()

    def setPhosphorAmt(self,amt):
        self.phosphorBlend = amt

    def setFont(self,font):
        self.fontChoice = font
        if self.textObject:
            self.textObject.setFont(font)
        self.update()

# --- PARAMETERS ---

class Parameter(QObject):
    uiType = ''
    def __init__(self,name,gObject,**kw):
        self.name = name
        self.gObject = gObject
        self.geometry = kw.get('geometry',False)
        self._currentValue = None
    def changeCB(self,value):
        self.set(value)
        #print "%s.changeCB(%s)" % (self.name,value)
    def set(self,value):
        self._currentValue = value
        self.updateUi()
    @property
    def value(self):
        return self._currentValue
    def setUiCallback(self,callback):
        self._uiCallback = callback
    def updateUi(self):
        if not hasattr(self,"_uiCallback"):
            print "no cb"
            QTimer.singleShot(1000, self.updateUi)
        else:
            self._uiCallback(self._currentValue)
            print "%s.updateUi() [%s]" % (self.name,self._currentValue)


class FloatParameter(Parameter):
    uiType = 'slider'
    def __init__(self, name, gObject, initValue=0.0, minValue=0.0, maxValue=1.0, log=False, format="%4.3f", **kw):
        super(FloatParameter,self).__init__(name,gObject,**kw)
        self.name = name
        self.set(initValue)
        self.minValue = minValue
        self.maxValue = maxValue
        self.log = log
        self.format = format

class StringParameter(Parameter):
    uiType = 'string'
    def __init__(self, name, gObject, value=[], **kw):
        super(StringParameter,self).__init__(name,gObject,**kw)
        self.name = name
        self.value = value
        self.set(value)

class ChoiceParameter(Parameter):
    uiType = 'combo'
    def __init__(self, name, gObject, choices=[], **kw):
        super(ChoiceParameter,self).__init__(name,gObject,**kw)
        self.name = name
        self.choices = choices
        self.set(choices[0])

class SwitchParameter(Parameter):
    uiType = 'checkbox'
    def __init__(self, name, gObject, bool, **kw):
        super(SwitchParameter,self).__init__(name,gObject,**kw)
        self.name = name
        self.set(bool)

class IntegerParameter(Parameter):
    uiType = 'spinbox'
    def __init__(self, name, gObject, initValue=24, minValue=1, maxValue=9999, step=24, **kw):
        super(IntegerParameter,self).__init__(name,gObject,**kw)
        self.name = name
        self.set(initValue)
        self.minValue = minValue
        self.maxValue = maxValue
        self.step = step

# --- WIDGETS ---

class WidgetSet(QGroupBox):
    def __init__(self,gObject,parent):
        super(WidgetSet,self).__init__(parent)
        self.setMinimumWidth(300)
        self.setTitle(gObject.name)
        self.gObject = gObject
        self.setLayout(QVBoxLayout())
        self.gridLayout = QGridLayout()
        self.layout().addLayout(self.gridLayout)
        self.layout().addStretch()
        self.rowIndex = 0

    def addParam(self,param):
        if param.uiType == 'slider':
            widget = self.addSlider(param.name, param.changeCB, param.value, param.minValue, param.maxValue, param.log, param.format)
        elif param.uiType == 'combo':
            widget = self.addCombo(param.name, param.changeCB, param.choices)
        elif param.uiType == 'checkbox':
            widget = self.addCheckbox(param.name, param.changeCB, param.value)
        elif param.uiType == 'spinbox':
            widget = self.addSpinbox(param.name, param.changeCB, param.value, param.minValue, param.maxValue, param.step)
        elif param.uiType == 'string':
            widget = self.addEntry(param.name, param.changeCB, param.value)
        widget.paramObj = param
        param.widgetSet = self
        param.gObject = self.gObject
        #param.setUiCallback(lambda value, w=widget: w.updateUiCB(value))
        param.setUiCallback(lambda value, o=param.gObject, n=param.name: o.updateParamValue(n,value))

    def addSlider(self,name,callback,initValue=None,minValue=0.0,maxValue=1.0,log=False,format="%g"):
        if initValue == None: initValue = maxValue
        def cb(valI):
            sW = self.sender()
            valF = sW.iToF(valI)
            try:
                callback(valF)
            except:
                pass
            sW.numberWidget.setText(format % valF)
            self.emit(SIGNAL("valueChanged()"))
        sliderW = FloatSlider(self)
        sliderW.setFloatRange(minValue,maxValue,log)
        numberW = QLabel()
        sliderW.numberWidget = numberW
        labelW  =QLabel(name)
        self.connect(sliderW,SIGNAL("valueChanged(int)"),cb)
        self.gridLayout.addWidget(sliderW, self.rowIndex,2)
        self.gridLayout.addWidget(numberW,self.rowIndex,1)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        self.rowIndex += 1
        sliderW.setFloatValue(initValue)
        #QTimer.singleShot(200, lambda c=callback, v=initValue: c(v))
        return sliderW

    def addCheckbox(self,name,callback,bool=False):
        def cb(val):
            sW = self.sender()
            callback(val)
            self.emit(SIGNAL("valueChanged()"))
        checkW = QCheckBox(self)
        labelW  =QLabel(name)
        self.connect(checkW,SIGNAL("stateChanged(int)"),cb)
        self.gridLayout.addWidget(checkW, self.rowIndex,1,Qt.AlignLeft)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        self.rowIndex += 1
        checkW.setCheckState((Qt.Unchecked,Qt.Checked)[int(initValue)!=0])
        #QTimer.singleShot(200, lambda c=callback, v=bool: c(v))
        return checkW

    def addEntry(self,name,callback,value=""):
        def cb(val):
            sW = self.sender()
            callback(val)
            self.emit(SIGNAL("valueChanged()"))
        entryW = QEntry(self)
        labelW  =QLabel(name)
        self.connect(checkW,SIGNAL("valueChanged(string)"),cb)
        self.gridLayout.addWidget(entryW, self.rowIndex,1,Qt.AlignLeft)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        self.rowIndex += 1
        entryW.set(value)
        #QTimer.singleShot(200, lambda c=callback, v=bool: c(v))
        return entryW

    def addCombo(self,name,callback,choices=[]):
        def cb(val):
            sW = self.sender()
            callback(str(val))
            self.emit(SIGNAL("valueChanged()"))
        comboW = QComboBox(self)
        comboW.addItems(choices)
        labelW  =QLabel(name)
        self.connect(comboW,SIGNAL("currentIndexChanged (const QString&)"),cb)
        self.gridLayout.addWidget(comboW, self.rowIndex,1,1,2)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        self.rowIndex += 1
        #QTimer.singleShot(200, lambda c=callback, v=choices[0]: c(v))
        return comboW

    def addSpinbox(self,name,callback,initValue=24,minValue=1,maxValue=9999,step=24):
        def cb(val):
            sW = self.sender()
            callback(val)
            self.emit(SIGNAL("valueChanged()"))
        spinW = QSpinBox(self)
        spinW.setRange(minValue,maxValue)
        spinW.setSingleStep(step)
        labelW  = QLabel(name)
        self.connect(spinW,SIGNAL("valueChanged (int)"),cb)
        self.gridLayout.addWidget(spinW, self.rowIndex,1,1,2)
        self.gridLayout.addWidget(labelW, self.rowIndex,0)
        self.rowIndex += 1
        #QTimer.singleShot(200, lambda c=callback, v=initValue: c(v))
        return spinW

class TimeDisplay(QLabel):
    def __init__(self,parent=None):
        super(TimeDisplay,self).__init__(parent)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.setSizePolicy(sizePolicy)
        self.setMaximumWidth(190)
        self.setMinimumHeight(20)
        self.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        font = QFont()
        font.setPointSize(20)
        #font.setBold(True)
        self.setFont(font)
        self.setText("0000")

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setWindowTitle('Martian')

        self.availableObjectTypes = { 
            "Circle":      CircleObject,
        }
        self.objectIndex = defaultdict(int)

        # Central widget
        self.centralW = QWidget(self)
        self.setCentralWidget(self.centralW)
        centralLayout = QVBoxLayout()
        self.centralW.setLayout(centralLayout)

        self.view = GraphicsWidget(self.centralW,main=self)
        centralLayout.addWidget(self.view)
        self.connect(self.view,SIGNAL("updateFrame(int)"),self.updateCB)

        # Tools
        self.makeToolBar()
        self.makeToolBox()
        self.makeMenus()

        self.statusBar().showMessage('Ready',2000)

    def updateCB(self,frameNumber):
        self.timeDisplay.setText("%04d" % frameNumber)

    def makeMenus(self):
        exit = QAction('Exit', self)
        exit.setShortcut('Ctrl+Q')
        exit.setStatusTip('Exit application')
        self.connect(exit, SIGNAL('triggered()'), SLOT('close()'))

        menubar = self.menuBar()
        file = menubar.addMenu('&Application')
        file.addAction(exit)

        view = menubar.addMenu("&View")
        toolboxViewAction = QAction('Toolbox', self)
        view.addAction(toolboxViewAction)
        def toolboxViewActionCB(b):
            self.toolboxDW.show()
        self.connect(toolboxViewAction,SIGNAL("triggered (bool)"),toolboxViewActionCB)

    def makeToolBar(self):
        self.toolbar = QToolBar(self)
        self.toolbar.setFloatable(True)
        self.toolbar.setMovable(True)
        #self.toolbar.setAllowedAreas(Qt.TopDockWidgetArea)
        self.addToolBar(Qt.TopToolBarArea,self.toolbar)

        self.playButton = QToolButton(self)
        self.playButton.setCheckable(True)
        self.playButton.setChecked(False)
        self.playButton.setAutoRaise(True)
        playPauseIcon = QIcon()
        playPauseIcon.addPixmap(QPixmap(os.path.join(iconPath, "play.png")),  QIcon.Normal, QIcon.Off)
        playPauseIcon.addPixmap(QPixmap(os.path.join(iconPath, "pause.png")), QIcon.Normal, QIcon.On)
        self.playButton.setIcon(playPauseIcon)
        self.playButton.setToolTip("Play/Pause")
        def playPauseCB(onOff):
            if onOff:
                self.view.timelineCB("play")
            else:
                self.view.timelineCB("pause")
        self.connect(self.playButton, SIGNAL("toggled(bool)"), playPauseCB)
        
        self.timeDisplay = TimeDisplay(self)

        self.toolbar.addAction(QIcon(os.path.join(iconPath, "camera.png")), "Save",      self.saveCB)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.timeDisplay)
        self.toolbar.addAction(QIcon(os.path.join(iconPath, "rewind.png")), "Rewind",    lambda : self.view.timelineCB("rewind"))
        self.toolbar.addAction(QIcon(os.path.join(iconPath, "stop.png")),   "Stop",      lambda : self.view.timelineCB("stop"))
        self.toolbar.addWidget(self.playButton)
        self.toolbar.addAction(QIcon(os.path.join(iconPath, "record.png")), "Record",    lambda : self.view.timelineCB("record"))

    def newObjectCB(self,objType, objClass):
        self.objectIndex[objType] += 1
        gObject = objClass()
        gObject.handle = self.objectIndex[objType]
        gObject.name = "%s%d" % (objType, self.objectIndex[objType])
        self.toolSwitchC.addItem(gObject.name)
        self.view.addObject(gObject)
        # Create tool page
        gObject.toolPageW = WidgetSet(gObject,self.toolPagesW)
        self.toolPagesW.addWidget(gObject.toolPageW)
        for param in gObject.params():
            gObject.toolPageW.addParam(param)
        self.connect(gObject.toolPageW, SIGNAL("valueChanged()"), self.view.update)

    def makeToolBox(self):
        # Dock widget for toolbox
        self.toolboxDW = QDockWidget("Toolbox")
        self.addDockWidget(Qt.LeftDockWidgetArea,self.toolboxDW)
        # Frame for contents of dock widget
        self.toolboxDW.setWidget( QWidget() )
        self.toolboxDW.widget().setLayout(QVBoxLayout())
        
        # Dock widget for objects
        self.objectsDW = QDockWidget("Objects")
        self.addDockWidget(Qt.LeftDockWidgetArea,self.objectsDW)
        # Frame for contents of dock widget
        self.objectsDW.setWidget( QWidget() )
        self.objectsW = self.objectsDW.widget()
        self.objectsW.setLayout(QVBoxLayout())
        # Frame for buttons
        self.buttonboxW = QWidget()
        self.buttonboxW.setLayout(QHBoxLayout())
        self.objectsW.layout().addWidget(self.buttonboxW)
        # Button to raise menu to allow creating new objects
        self.newObjectB = QPushButton(QString("New"))
        self.buttonboxW.layout().addWidget(self.newObjectB)
        self.newObjectB.setStatusTip('Create new object')
        
        # Combo to flip between objects/tool sets
        self.toolSwitchC = QComboBox()
        self.buttonboxW.layout().addWidget(self.toolSwitchC)

        #self.delObjectB = QPushButton(QString("Delete"))
        #self.buttonboxW.layout().addWidget(self.delObjectB)
        #self.delObjectB.setStatusTip('Delete object')

        newM = QMenu(self.newObjectB)
        for objType, objClass in self.availableObjectTypes.items():
            a = QAction(objType, self)
            self.connect(a, SIGNAL('triggered()'), lambda s=self,o=objType, c=objClass: s.newObjectCB(o,c))
            newM.addAction(a)
        self.newObjectB.setMenu(newM)

        # Stacked pages to hold each widget's toolset
        self.toolPagesW = QStackedWidget(self.objectsW)
        self.objectsW.layout().addWidget(self.toolPagesW)
        #self.objectsW.layout().setStretch(2,1)
        self.connect(self.toolSwitchC,SIGNAL("activated(int)"),self.toolPagesW.setCurrentIndex)
        # toolbox
        
        #self.toolbox.setMinimumWidth(300)
        #self.toolbox.sizeHint = lambda : QSize(220,500)

    def saveCB(self):
        for gObject in self.view.objects.values():
            print gObject
        #savePixmap = QPixmap.grabWindow(self.view.winId())
        #filePath   = QFileDialog.getSaveFileName(self, "Save image", "", "Image Files (*.png *.jpg *.bmp)")
        #savePixmap = QPixmap.grabWidget(self.view)
        #savePixmap.save(filePath)


if __name__ == '__main__':
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
