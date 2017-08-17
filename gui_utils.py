import sys,struct,os,math
import numpy as np
sys.path.append("../board")
sys.path.append("..\\")
#sys.path.append("..\\..\\")
from PyQt4 import QtCore, QtGui, uic
import xml.etree.ElementTree as ET


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

def xmlparser(config_file):
    tree = ET.parse(config_file)
    root = tree.getroot()
    tpm_list=[]
    for node in tree.iter('iTPM'):
        tpm_elem={}
        for tpm in node:
            tpm_elem[tpm.tag] = tpm.text
        tpm_list += [tpm_elem]
    return tpm_list


def clickable(widget):
    class Filter(QtCore.QObject):
        clicked = QtCore.pyqtSignal()
        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QtCore.QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        return True
            return False
    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked

# Matplotlib stuff
import matplotlib
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar

#from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
#from matplotlib.backends.backend_gtkagg import NavigationToolbar2GTKAgg as NavigationToolbar

# Other stuff

NAME_FILTER = [[ "F1",  5,   48,   80], 
               [ "F2",  3,   80,  120],  
               [ "F3",  1,  120,  200],  
               [ "F4",  0,  200,  280],  
               [ "F5",  2,  280,  450],  
               [ "F6",  4,  450,  780],  
               [ "F7",  6,  780, 1450],  
               [ "F0",  7,    0,    0]]

FILTER_REVERSE_MAP=[3,2,4,1,5,0,6,7]


try:
    # for Python2
    from Tkinter import *
except ImportError:
    # for Python3
    from tkinter import * 


def colors(name):
    if name == "white_on_red":
        return "background-color: rgb(255, 20, 20); color: rgb(255, 255, 255)"
    elif name == "black_on_yellow":
        return "background-color: rgb(255, 255, 0); color: rgb(0, 0, 0)"
    elif name == "black_on_green":
        return "background-color: rgb(0, 255, 0); color: rgb(0, 0, 0)"
    elif name == "black_on_blue":
        return "background-color: rgb(85, 170, 255); color: rgb(0, 0, 0)"

def calc_spectra(vett):
    spettro=np.zeros(len(vett)/2)

    window = np.hanning(len(vett))
    spettro = np.fft.rfft(vett*window)
    N = len(spettro)
    acf = 2  #amplitude correction factor
    spettro = abs((acf*spettro)/N)
    spettro = 20*np.log10(spettro/127.0)

    x = np.arange(0,len(vett),1)
    freq = np.fft.rfftfreq(x.shape[-1])
    freqs = freq*sample_rate

    return (freqs,spettro)

class MplCanvas(FigureCanvas):

    def __init__( self , parent = None, dpi = 100, size = (5.95,3.4)):
        self.dpi = dpi
        self.fig = Figure(size, dpi = self.dpi, facecolor='white')
        #?self.axes1  = self.fig.add_subplot( 111 )
        self.axes1  = self.fig.add_axes( [0.12, 0.12, 0.84, 0.8] )
        self.axes1.xaxis.set_label_text("MHz", fontsize=10)
        self.axes1.yaxis.set_label_text("dB", fontsize=10)
        self.axes1.set_axis_bgcolor('white')
        self.axes1.tick_params(axis='both', which='both', labelsize=10)
        #self.axes1.tick_params(axis='both', which='major', labelsize=10)
        self.axes1.set_ylim([-100, 0])
        self.axes1.set_xlim([0, 400])


        FigureCanvas.__init__( self, self.fig )
        FigureCanvas.setSizePolicy( self, QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding )
        FigureCanvas.updateGeometry( self )

class MatplotlibPlot(QtGui.QWidget):
    """ Class encapsulating a matplotlib plot"""
    def __init__( self, parent = None ):
        QtGui.QWidget.__init__( self, parent )
    #def __init__(self, parent = None, dpi = 100, size = (6.1,4)):
        """ Class initialiser """

        #self.dpi = dpi
        #self.figure = Figure(size, dpi = self.dpi, facecolor='white')
        self.canvas = MplCanvas() #create canvas that will hold our plot
        self.navi_toolbar = NavigationToolbar(self.canvas, self) #createa navigation toolbar for our plot canvas
        
        #self.canvas = FigureCanvas(self.figure)
        #self.canvas.setParent(parent)
        #self.navi_toolbar = NavigationToolbar(self.canvas, self)

        self.updateGeometry()
        self.vbl = QtGui.QVBoxLayout()
        self.vbl.addWidget( self.canvas )
        #self.vbl.addSpacing(20)
        self.vbl.addWidget(self.navi_toolbar)
        self.setLayout( self.vbl )
        self.show()
        self.plotClear()



    def resetSubplots(self):
        self.nSubplot=0

    def plotCurve(self, assex, data, xAxisRange = None, yAxisRange = None, xLabel = "", yLabel = "", title="", label="", plotLog=False, nSubplots=1, hold=False):
        """ Plot the data as a curve"""

        if len(data) != 0:
            # Plan what dimensions the grid will have if there are to be subplots
            # Attempt to be roughly square but give preference to vertical stacking
            nSubplots_v = np.ceil(np.sqrt(nSubplots))
            nSubplots_h = np.ceil(float(nSubplots)/nSubplots_v)

            auto_scale_y = True            
            #yAxisRange=np.array(yAxisRange)
            #if yAxisRange is not None:
            #    auto_scale_y = False
            #    if plotLog:
            #        data[data==0] = 1
            #        yAxisRange[yAxisRange==0] = 1
            #        data= 10*np.log(data)
            #        yAxisRange = 10*np.log(yAxisRange)
            #else:
            #    auto_scale_y = True
                
            #f, ax = plt.subplots()
            #self.axes1 = self.figure.add_subplot(111)
            #self.canvas.axes1.set_title(title, fontsize=10)
            self.canvas.axes1.plot(assex, data, scaley=auto_scale_y)

            self.canvas.axes1.xaxis.set_label_text(xLabel, fontsize=10)
            self.canvas.axes1.yaxis.set_label_text(yLabel, fontsize=10)
            self.canvas.axes1.set_axis_bgcolor('white')
            self.canvas.axes1.tick_params(axis='both', which='minor', labelsize=10)
            self.canvas.axes1.tick_params(axis='both', which='major', labelsize=10)
            self.canvas.axes1.set_ylim(yAxisRange)

            #self.axes2 = self.figure.add_subplot(212)
            #self.axes2.set_title("Secondo grafico", fontsize=12)
            #self.axes2.plot(range(np.size(data)), data, scaley=auto_scale_y)

            #self.axes2.xaxis.set_label_text(xLabel, fontsize=6)
            #self.axes2.yaxis.set_label_text(yLabel, fontsize=6)
            #self.axes2.set_axis_bgcolor('white')
            #self.axes2.tick_params(axis='both', which='minor', labelsize=10)
            #self.axes2.tick_params(axis='both', which='major', labelsize=10)
            #self.canvas.figure.tight_layout()
            self.updatePlot()


    def updatePlot(self):
        self.canvas.draw()
        self.show()
        
    def plotClear(self):
        # Reset the plot landscape
        self.canvas.axes1.clear()
        self.updatePlot()
        #self.canvas.fig.show()
        #self.show()

class MiniCanvas(FigureCanvas):

    def __init__( self , nplot, parent = None, dpi = 100, size = (11,5.7)):
        self.nplot=nplot
        self.dpi = dpi
        self.fig = Figure(size, dpi = self.dpi, facecolor='white')
        self.fig.set_tight_layout(True)
        self.ax = []
        #print self.nplot,math.sqrt(self.nplot)
        for i in xrange(self.nplot):
            self.ax += [self.fig.add_subplot(math.sqrt(self.nplot),math.sqrt(self.nplot),i+1)]
            #self.ax[i].xaxis.set_label_text("MHz", fontsize=7)
            #self.ax[i].yaxis.set_label_text("dB", fontsize=9)
            self.ax[i].set_axis_bgcolor('white')
            #self.ax[i].tick_params(axis='both', which='minor', labelsize=8)
            self.ax[i].tick_params(axis='both', which='both', labelsize=8)
            self.ax[i].set_ylim([-100, 0])
            self.ax[i].set_xlim([50, 100])

        FigureCanvas.__init__( self, self.fig )
        FigureCanvas.setSizePolicy( self, QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding )
        FigureCanvas.updateGeometry( self )

class MiniPlots(QtGui.QWidget):
    """ Class encapsulating a matplotlib plot"""
    def __init__( self, parent = None , nplot = 16):
        QtGui.QWidget.__init__( self, parent )
    #def __init__(self, parent = None, dpi = 100, size = (6.1,4)):
        """ Class initialiser """
        self.nplot = nplot
        #print self.nplot
        self.canvas = MiniCanvas(self.nplot) #create canvas that will hold our plot
        self.updateGeometry()
        self.vbl = QtGui.QVBoxLayout()
        self.vbl.addWidget( self.canvas )
        self.setLayout( self.vbl )
        self.show()

    def resetSubplots(self):
        self.nSubplot=0

    def plotCurve(self, assex, data, ant, xAxisRange = None, yAxisRange = None, xLabel = "", yLabel = "", title="", label="", plotLog=False, nSubplots=1, hold=False, colore="b"):
        """ Plot the data as a curve"""
        if len(data) != 0:
            #auto_scale_y = True
            #self.canvas.ax[ant].clear()
            self.canvas.ax[ant].plot(assex, data, scaley=False, color=colore)
            #self.canvas.ax[ant].set_xlim([50, 100])
            #print "plot ", len(assex), len(data), ant

    def updatePlot(self):
        self.canvas.draw()
        self.show()
        
    def plotClear(self):
        # Reset the plot landscape
        for i in xrange(self.nplot):
             self.canvas.ax[i].clear()
        self.updatePlot()

class BarCanvas(FigureCanvas):

    def __init__( self , parent = None, dpi = 100, size = (11,5.7)):
        self.dpi = dpi
        self.fig = Figure(size, dpi = self.dpi, facecolor='white')
        self.fig.set_tight_layout(True)
        self.ax = self.fig.add_subplot(1,1,1)
        self.ax.set_axis_bgcolor('white')
        self.ax.tick_params(axis='both', which='both', labelsize=8)
        #self.ax.tick_params(axis='both', which='major', labelsize=8)
        self.ax.set_xticks(xrange(33))
        self.ax.set_yticks([5,10,15,20,25,30,35])
        self.ax.set_ylim([0, 40])
        self.ax.set_xlim([0, 17])

        FigureCanvas.__init__( self, self.fig )
        FigureCanvas.setSizePolicy( self, QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding )
        FigureCanvas.updateGeometry( self )

class BarPlot(QtGui.QWidget):
    """ Class encapsulating a matplotlib plot"""
    def __init__( self, parent = None):
        QtGui.QWidget.__init__( self, parent )
    #def __init__(self, parent = None, dpi = 100, size = (6.1,4)):
        """ Class initialiser """
        #print self.nplot
        self.canvas = BarCanvas() #create canvas that will hold our plot
        self.updateGeometry()
        self.vbl = QtGui.QVBoxLayout()
        self.vbl.addWidget( self.canvas )
        self.setLayout( self.vbl )
        self.show()
        self.ind = np.arange(16)

    def resetSubplots(self):
        self.nSubplot=0

    def plotBar(self, data):
        """ Plot the data as Bars"""
        if len(data) != 0:
            self.canvas.ax.clear()
            self.canvas.ax.set_axis_bgcolor('white')
            self.canvas.ax.tick_params(axis='both', which='both', labelsize=10)
            #self.canvas.ax.tick_params(axis='both', which='major', labelsize=10)
            self.canvas.ax.set_xticks(xrange(17))
            self.canvas.ax.set_yticks([15,20])
            self.canvas.ax.set_ylim([0, 40])
            self.canvas.ax.set_xlim([0, 17])
            self.canvas.ax.set_xlabel("ANTENNA")
            self.canvas.ax.set_ylabel("ADU RMS")
            self.canvas.ax.grid()
            rects1 = self.canvas.ax.bar(self.ind+0.6, data[0::2], 0.4, color='b')
            rects2 = self.canvas.ax.bar(self.ind+1, data[1::2], 0.4, color='g')
            self.updatePlot()

    def updatePlot(self):
        self.canvas.draw()
        self.show()
        
    def plotClear(self):
        # Reset the plot landscape
        self.canvas.ax.clear()
        self.updatePlot()




