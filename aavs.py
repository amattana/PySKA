#!/usr/bin/env python

'''

  GUI App for debugging AAVS1 antennas during installation on the MRO field

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2017, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"


from PyQt4 import QtCore, QtGui, uic
import sys, os, socket
sys.path.append("../board")
sys.path.append("../rf_jig")
sys.path.append("../config")
sys.path.append("../repo_utils")
#sys.path.append("../board/pyska")
from tpm_utils import *
#from ska_tpm import xmlparser
#from jig_adu_test import *
from bsp.tpm import *
#import config.manager as config_man
import manager as config_man
from netproto.sdp_medicina import sdp_medicina as sdp_med
import subprocess
DEVNULL = open(os.devnull,'w')

import datetime, time
import sys, easygui, datetime
#from qt_rf_jig_utils import *
from gui_utils import *
from rf_jig import *
from rfjig_bsp import *
from ip_scan import *

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import httplib2
from openpyxl import load_workbook

# Matplotlib stuff
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Other stuff
import numpy as np
import struct

#import multiprocessing
from threading import Thread

# Some globals

DEBUG = True

COLORS = ['b','g','r','c','m','y','k','w']
RIGHE = 257
COLONNE = 12
EX_FILE = "/home/mattana/Downloads/AAVS 1.1 Locations and connections.xlsx"
OUTPUT_PICTURE_DATA_PATH = "/home/mattana/Documents/AAVS-DATA/"
LOG_PATH = "/home/mattana/aavs_data"

LABEL_WIDTH  = 23
LABEL_HEIGHT = 15
TEXT_WIDTH   = 50
TEXT_HEIGHT  = 22
FLAG_WIDTH   = 25
FLAG_HEIGHT  = 16

TABLE_HSPACE = 430
TABLE_VSPACE = 30

import urllib3
# Test application, security unimportant:
urllib3.disable_warnings()

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

colori=[['        RMS > 30  ','#c800c8'], ['25 < RMS < 30','#ff1d00'], ['20 < RMS < 25','#ff9f00'], ['15 < RMS < 20','#22ff00'], ['10 < RMS < 15','#00ffc5'], ['  5 < RMS < 10 ','#00c5ff'],['    0 < RMS < 5','#0000ff']]

def read_from_google():
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("AAVS 1.1 Locations and connections").sheet1


    # Extract and print all of the values
    cells = sheet.get_all_records()
    return cells


def read_from_local():
    if (os.path.isfile(EX_FILE)):
        wb2 = load_workbook(EX_FILE, data_only=True)
        ws = wb2.active
        wb2.close()
        keys=[]
        for j in range(COLONNE):
            keys += [ws.cell(row=1, column=j+1).value]

        cells=[]
        for i in range(RIGHE-1):
            dic={}
            for j in range(COLONNE):
                val=ws.cell(row=i+2, column=j+1).value
                if not val==None:
                    dic[keys[j]]=val
                else:
                    dic[keys[j]]=""
            cells += [dic]
    else:
        print "Unable to find file:", EX_FILE
        print "\nExiting with errors...\n"
        exit()
    return cells


# This creates the input label (eg: for input 15 -> "15:")
def create_label(Dialog, x, y, w, h, text):
    label = QtGui.QLabel(Dialog)
    label.setGeometry(QtCore.QRect(x, y, w, h))
    label.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
    label.setText(_translate("Dialog", text, None))
    label.setFont(QtGui.QFont("Ubuntu",9))
    return label

def create_flag(Dialog, x, y, color, text):
    flag = QtGui.QLabel(Dialog)
    flag.setGeometry(QtCore.QRect(x, y, FLAG_WIDTH, FLAG_HEIGHT))
    flag.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    flag.setAutoFillBackground(True)
    if color=="green":
        flag.setStyleSheet(_fromUtf8("background-color: rgb(0, 170, 0);"))
    elif color=="yellow":
        flag.setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 0);"))
    elif color=="cyan":
        flag.setStyleSheet(_fromUtf8("background-color: rgb(0, 255, 234);"))
        flag.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
    else:
        flag.setStyleSheet(_fromUtf8("background-color: rgb(255, 0, 0);"))
    flag.setAlignment(QtCore.Qt.AlignCenter)
    flag.setText(_translate("Dialog", text, None))
    return flag

def create_button(Dialog, x, y, text):
    qbutton = QtGui.QPushButton(Dialog)
    qbutton.setGeometry(QtCore.QRect(x, y, 40, 16))
    qbutton.setText(_translate("Dialog", text, None))
    return qbutton

def create_record(i,diz):
    wid = QtGui.QFrame()
    wid.setFrameShape(1)
    wid.setFixedSize(710,20)
    create_label(wid, 8, 2, 15, 18, str(i))
    create_label(wid, 35, 2, 30, 18, str(diz['Base']))
    create_label(wid, 82, 2, 30, 18, str(diz['Hybrid Cable']))
    create_label(wid, 120, 2, 30, 18, str(diz['Roxtec']))
    create_label(wid, 155, 2, 30, 18, str(diz['Ribbon']))
    create_label(wid, 190, 2, 30, 18, str(diz['Fibre']))
    create_label(wid, 230, 2, 50, 18, str(diz['Colour']))
    create_label(wid, 290, 2, 20, 18, str(diz['TPM']))
    create_label(wid, 320, 2, 20, 18, str(diz['RX']))
    create_flag(wid, 360, 2, "yellow", "N")
    create_flag(wid, 390, 2, "green", "S")
    create_flag(wid, 420, 2, "green", "D")
    create_flag(wid, 450, 2, "green", "F")
    create_flag(wid, 480, 2, "green", "G")
    create_flag(wid, 510, 2, "green", "C")
    create_flag(wid, 540, 2, "green", "P")
    create_flag(wid, 570, 2, "green", "R")
    create_button(wid, 610, 2, "Plot")
    create_button(wid, 650, 2, "Att")
    return wid


    # rec['Roxtec'] = create_label(Dialog, 270, 90, diz['Roxtec'])
    # rec['Ribbon'] = create_label(Dialog, 270, 90, diz['Ribbon'])
    # rec['Fibre'] = create_label(Dialog, 270, 90, diz['Fibre'])
    # rec['Colour'] = create_label(Dialog, 270, 90, diz['Colour'])
    # rec['East'] = create_label(Dialog, 270, 90, diz['East'])
    # rec['North'] = create_label(Dialog, 270, 90, diz['North'])

    #rec['value'] = create_label(Dialog, 45+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "0")
    #rec['text'] = create_text(Dialog,  80+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "0")
    #rec['minus'] = create_button(Dialog,  140+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "-")
    #rec['plus'] = create_button(Dialog,  170+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "+")
    #rec['lo'] = create_flag(Dialog, 210+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "green", "LO")
    #rec['hi'] = create_flag(Dialog, 260+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "yellow", "HI")
    #rec['rf'] = create_flag(Dialog, 310+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "green", rf_map[1])
    #rec['of'] = create_flag(Dialog, 360+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "cyan", rf_map[2])
    #return rec

def font_bold():
    font = QtGui.QFont()
    font.setBold(True)
    font.setWeight(75)
    return font
def font_normal():
    font = QtGui.QFont()
    return font



class AAVS(QtGui.QMainWindow):

    """ Main UI Window class """

    # Signal for Slots
    #housekeeping_signal = QtCore.pyqtSignal()
    #jig_pm_signal = QtCore.pyqtSignal()
    #antenna_test_signal = QtCore.pyqtSignal()

    def __init__(self, uiFile):
        """ Initialise main window """
        super(AAVS, self).__init__()

        # Load window file
        self.mainWidget = uic.loadUi(uiFile)
        self.setCentralWidget(self.mainWidget)
        self.setWindowTitle("AAVS")
        self.resize(1100,680)

        self.debug = DEBUG

        print "The program is running with flag DEBUG set to:",self.debug 

        #self.pic_ska = QtGui.QLabel(self.mainWidget.qtab_conf)
        #self.pic_ska.setGeometry(590, 300, 480, 200)
        #self.pic_ska.setPixmap(QtGui.QPixmap(os.getcwd() + "/pic/ska_inaf_logo2.jpg"))
        #self.mainWidget.qframe_ant_rms.hide()

        self.cells = []
        self.TPMs=[]

        self.gb = self.mainWidget.cb_group.isChecked()
        self.gb_not = self.mainWidget.cb_not.isChecked()
        self.gb_single = self.mainWidget.cb_single.isChecked()
        self.gb_double = self.mainWidget.cb_double.isChecked()
        self.gb_ferrite = self.mainWidget.cb_ferrite.isChecked()
        self.gb_gnd = self.mainWidget.cb_gnd.isChecked()
        self.gb_condom = self.mainWidget.cb_condom.isChecked()
        self.gb_capacitor = self.mainWidget.cb_capacitor.isChecked()
        self.gb_feed = self.mainWidget.cb_feed.isChecked()

        self.load_events()
        self.loadAAVSdata()

        self.log = True

        if self.log:
            for tpm in self.TPMs:
                directory = LOG_PATH + "/" + tpm['IP']
                if not os.path.exists(directory):
                    os.makedirs(directory)

        self.mapPlot = MapPlot(self.mainWidget.plotWidgetMap)
        self.mapPlot.plotClear()
        self.runMap()
        self.show()

    def load_events(self):
        self.mainWidget.button_runMap.clicked.connect(lambda: self.runMap())
        self.mainWidget.button_saveMap.clicked.connect(lambda: self.saveMap())

    def runMap(self):
        print "RUN MAP"
        self.map_polx = self.mainWidget.cb_polx.isChecked()
        self.map_poly = self.mainWidget.cb_poly.isChecked()
        if self.map_poly:
            self.pol=1
        else:
            self.pol=0

        if self.mainWidget.cb_rms.isChecked():
            self.map_meas = 'RMS'
        else:
            self.map_meas = 'DBM'
        self.map_dBm = self.mainWidget.cb_dBm.isChecked()
        self.map_base = self.mainWidget.cb_base.isChecked()
        self.map_tpm = self.mainWidget.cb_tpm.isChecked()

        self.mapPlot.plotMap(self.cells, marker='8', markersize=12, color='k')
        self.mapPlot.plotMap(self.cells, marker='8', markersize=10, color='w')


        for tpm in self.TPMs:
            if len(tpm['ANTENNE'])>0:
                rms,dbm = get_raw_meas(tpm, meas=self.map_meas, debug=self.debug)
            #print len(tpm['ANTENNE']), len(rms)
            for j in range(len(tpm['ANTENNE'])):
                if (tpm['ANTENNE'][j]['Power']==""):
                    x = float(str(tpm['ANTENNE'][j]['East']).replace(",", "."))
                    y = float(str(tpm['ANTENNE'][j]['North']).replace(",", "."))
                    tpm['ANTENNE'][j]['RMS-X']=rms[(j*2)]
                    tpm['ANTENNE'][j]['RMS-Y']=rms[(j*2)+1]
                    tpm['ANTENNE'][j]['DBM-X']=dbm[(j*2)]
                    tpm['ANTENNE'][j]['DBM-Y']=dbm[(j*2)+1]
                    if (rms[(j*2)] > 90) or (rms[(j*2)+1] > 90):
                        self.plotOscilla( x, y)
                    else:   
                        if self.map_meas=="RMS":
                            self.mapPlot.oPlot(x, y, marker='8', markersize=10, color=rms_color(rms[(j*2)+self.pol]))
                        else:
                            self.mapPlot.oPlot(x, y, marker='8', markersize=10, color=rms_color(dbm[(j*2)+self.pol]))
                    if self.log:
                        self.logMeas(tpm['IP'], tpm['ANTENNE'][j])
#                    print("Plotting Antenna "+str(tpm['ANTENNE'][j]['Base'])+" (RX: "+str(tpm['ANTENNE'][j]['RX'])+", J:"+str(j)+", Colour: "+tpm['ANTENNE'][j]['Colour']+") with RMS %4.1f"%(rms[(j*2)+self.pol])+" and power of %4.1f dBm"%(dbm[(j*2)+self.pol]))
                    print("Plotting Antenna "+str(tpm['ANTENNE'][j]['Base'])+" with RMS %4.1f"%(rms[(j*2)+self.pol])+" and power of %4.1f dBm"%(dbm[(j*2)+self.pol]))
                else:
                    print("Plotting Antenna "+str(tpm['ANTENNE'][j]['Base'])+" Powered OFF")
                    x = float(str(tpm['ANTENNE'][j]['East']).replace(",", "."))
                    y = float(str(tpm['ANTENNE'][j]['North']).replace(",", "."))
                    self.mapPlot.oPlot(x, y, marker='8', markersize=10, color='k')

    def plotOscilla(self, x, y):
        self.mapPlot.oPlot(x, y, marker='8', markersize=14, color='k')
        self.mapPlot.oPlot(x, y, marker='8', markersize=12, color='y')
        self.mapPlot.oPlot(x, y, marker='8', markersize=9, color='k')
        self.mapPlot.oPlot(x, y, marker='8', markersize=6, color='y')
        self.mapPlot.oPlot(x, y, marker='8', markersize=3, color='k')
        self.mapPlot.oPlot(x, y, marker='8', markersize=2, color='y')


    def logMeas(self, ip, ant):
        filename = LOG_PATH+"/"+ip+"/ANTENNA-%03d.tsv"%(int(ant['Base']))
        if os.path.exists(filename):
            append_write = 'a' # append if already exists
        else:
            append_write = 'w' # make a new file if not
        #print filename
        with open(filename, append_write) as f:
            f.write(datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()),"%Y-%m-%d %H:%M:%S\t")+"%4.1f\t%4.1f\t%4.1f\t%4.1f\n"%(ant['RMS-X'],ant['RMS-Y'],ant['DBM-X'],ant['DBM-Y']))

    def saveMap(self):
        print "SAVE MAP"

    def plotMap(self):
        print "PLOT MAP"

    def loadAAVSdata(self):
        try:
            self.cells = read_from_google()
            print "\nSuccessfully connected to the online google spreadsheet!\n\n"

        except httplib2.ServerNotFoundError:
            print("\nUnable to find the server at accounts.google.com.\n\nContinuing with localfile: %s\n"%(EX_FILE))
            self.cells = read_from_local()
            print "done!"

        if self.debug:
            tpms=['10.0.10.6']
        else:
            tpms=ip_scan()

        self.TPMs=[]
        for i in tpms:
            tpm = {}
            tpm['TPM'] = TPM(ip=i, port=10000, timeout=1)
            tpm['IP']  = i
            tpm['ANTENNE'] = [x for x in self.cells if x['TPM']==int(i.split(".")[-1])]
            self.TPMs += [tpm]
        print("Loaded objects of %d TPM"%(len(self.TPMs)))

        mygroupbox = QtGui.QGroupBox()
        myform = QtGui.QFormLayout()
        myform.setVerticalSpacing(0)
        myform.setHorizontalSpacing(0)
        for i in xrange(len(self.cells)):
            myform.addRow(create_record(i, self.cells[i]))
            #myform.addRow(QtGui.QLabel("Ciao"))
        mygroupbox.setLayout(myform)
        self.mainWidget.qscroll_aavs.setWidget(mygroupbox)
        self.mainWidget.qscroll_aavs.setWidgetResizable(True)
        self.mainWidget.qscroll_aavs.setFixedHeight(221)
        #print("len(self.cells)=%d"%len(self.cells))

if __name__ == "__main__":
    os.system("python ../config/setup.py")
    app = QtGui.QApplication(sys.argv)
    window = AAVS("aavs.ui")

    #window.housekeeping_signal.connect(window.updateHK)
    #window.jig_pm_signal.connect(window.updateJIGpm)
    #window.antenna_test_signal.connect(window.updateAntennaTest)

    sys.exit(app.exec_())
