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

from optparse import OptionParser

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

COLORS = ['b','g','r','c','m','y','k','w']
RIGHE = 257
COLONNE = 12
EX_FILE = "/home/mattana/Downloads/AAVS 1.1 Locations and connections.xlsx"
OUTPUT_PICTURE_DATA_PATH = "/home/mattana/Documents/AAVS-DATA/"
LOG_PATH = "/home/mattana/aavs_data"
PATH_PLOT_LIST = "./.plotlists/"
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
    record = {}

    record['frame'] = QtGui.QFrame()
    record['frame'].setFrameShape(1)
    record['frame'].setFixedSize(960,20)
    create_label(record['frame'], 8, 2, 15, 18, str(i))
    record['Base']=int(diz['Base'])
    record['TPM']=diz['TPM']
    record['RX']=diz['RX']
    create_label(record['frame'], 35, 2, 30, 18, str(int(diz['Base'])))
    if not diz['Hybrid Cable']=="":
        create_label(record['frame'], 82, 2, 30, 18, str(int(diz['Hybrid Cable'])))
    if not diz['Roxtec']=="":
        create_label(record['frame'], 120, 2, 30, 18, str(int(diz['Roxtec'])))
    if not diz['Ribbon']=="":
        create_label(record['frame'], 155, 2, 30, 18, str(int(diz['Ribbon'])))
        create_label(record['frame'], 190, 2, 30, 18, str(int(diz['Fibre'])))
    create_label(record['frame'], 230, 2, 50, 18, str(diz['Colour']))
    if not diz['TPM']=="":
        create_label(record['frame'], 290, 2, 20, 18, str(int(diz['TPM'])))
        create_label(record['frame'], 320, 2, 20, 18, str(int(diz['RX'])))
    create_flag(record['frame'], 380, 2, "yellow", "N")
    create_flag(record['frame'], 410, 2, "green", "S")
    create_flag(record['frame'], 440, 2, "green", "D")
    create_flag(record['frame'], 470, 2, "green", "F")
    create_flag(record['frame'], 500, 2, "green", "G")
    create_flag(record['frame'], 530, 2, "green", "C")
    create_flag(record['frame'], 560, 2, "green", "P")
    create_flag(record['frame'], 590, 2, "green", "R")
    record['add']=create_button(record['frame'], 650, 2, "Plot")
    record['att']=create_button(record['frame'], 690, 2, "Att")

    return record


def create_plot_record(ant, cells):
    record = {}
    diz = [x for x in cells if x['Base']==ant][0]
    record['frame'] = QtGui.QFrame()
    record['frame'].setFrameShape(1)
    record['frame'].setFixedSize(960,20)
    #create_label(record['frame'], 8, 2, 15, 18, str(i))
    record['Base']=int(diz['Base'])
    record['TPM']=diz['TPM']
    record['RX']=diz['RX']
    create_label(record['frame'], 35, 2, 30, 18, str(int(diz['Base'])))
    if not diz['Hybrid Cable']=="":
        create_label(record['frame'], 82, 2, 30, 18, str(int(diz['Hybrid Cable'])))
    if not diz['Roxtec']=="":
        create_label(record['frame'], 120, 2, 30, 18, str(int(diz['Roxtec'])))
    if not diz['Ribbon']=="":
        create_label(record['frame'], 155, 2, 30, 18, str(int(diz['Ribbon'])))
        create_label(record['frame'], 190, 2, 30, 18, str(int(diz['Fibre'])))
    create_label(record['frame'], 230, 2, 50, 18, str(diz['Colour']))
    if not diz['TPM']=="":
        create_label(record['frame'], 290, 2, 20, 18, str(int(diz['TPM'])))
        create_label(record['frame'], 320, 2, 20, 18, str(int(diz['RX'])))
    create_flag(record['frame'], 380, 2, "yellow", "N")
    create_flag(record['frame'], 410, 2, "green", "S")
    create_flag(record['frame'], 440, 2, "green", "D")
    create_flag(record['frame'], 470, 2, "green", "F")
    create_flag(record['frame'], 500, 2, "green", "G")
    create_flag(record['frame'], 530, 2, "green", "C")
    create_flag(record['frame'], 560, 2, "green", "P")
    create_flag(record['frame'], 590, 2, "green", "R")
    record['Color']=create_color_list(record['frame'],640,1)

    return record

def create_color_list(frame,x,y):
    listacolori=QtGui.QComboBox(frame)
    listacolori.addItem("blue")
    listacolori.addItem("green")
    listacolori.addItem("red")
    listacolori.addItem("black")
    listacolori.addItem("yellow")
    listacolori.addItem("cyan")
    listacolori.setGeometry(QtCore.QRect(x, y, 100, 18))
    listacolori.setFont(QtGui.QFont("Ubuntu", 9))
    return listacolori



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

    def __init__(self, uiFile, flag_debug=False):
        """ Initialise main window """
        super(AAVS, self).__init__()

        # Load window file
        self.mainWidget = uic.loadUi(uiFile)
        self.setCentralWidget(self.mainWidget)
        self.setWindowTitle("AAVS")
        self.resize(1100,680)

        self.debug = flag_debug

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
        self.switchtox = False
        self.switchtoy = False
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
        self.mapPlot.canvas.mpl_connect('button_press_event', self.onclick)
        self.show()

        self.initPlotList()
        self.updatePlotList()

        self.spectraPlot = MiniPlots(self.mainWidget.plotWidgetSpectra, 16, dpi=92)
        #self.spectraPlot.plotClear()


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

        spente=[a for a in self.cells if "OFF" in a['Power']]
        self.mapPlot.plotMap(spente, marker='+', markersize=11, color='k')


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
                    if (rms[(j*2)] > 105) or (rms[(j*2)+1] > 105):
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
        if not self.debug:
            try:
                self.cells = read_from_google()
                print "\nSuccessfully connected to the online google spreadsheet!\n\n"

            except httplib2.ServerNotFoundError:
                print("\nUnable to find the server at accounts.google.com.\n\nContinuing with local file: %s\n"%(EX_FILE))
                self.cells = read_from_local()
                print "done!"
            tpms = ip_scan()
        else:
            print("\nReading local file: %s\n" % (EX_FILE))
            self.cells = read_from_local()
            tpms=['10.0.10.6']

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
        self.records = []
        for i in xrange(len(self.cells)):
            self.records += [create_record(i, self.cells[i])]
            ant=int(self.records[i]['Base'])
            self.records[i]['add'].clicked.connect(lambda status, g=ant: self.addPlot(g))
            self.records[i]['att'].clicked.connect(lambda status, g=ant: self.openPreadu(g))

            myform.addRow(self.records[i]['frame'])
            #myform.addRow(QtGui.QLabel("Ciao"))
        mygroupbox.setLayout(myform)
        self.mainWidget.qscroll_aavs.setWidget(mygroupbox)
        self.mainWidget.qscroll_aavs.setWidgetResizable(True)
        self.mainWidget.qscroll_aavs.setFixedHeight(221)
        #print("len(self.cells)=%d"%len(self.cells))

    def initPlotList(self):
        self.plotRecords = QtGui.QGroupBox()
        myform2 = QtGui.QFormLayout()
        myform2.setVerticalSpacing(0)
        myform2.setHorizontalSpacing(0)
        #myform.addRow()
        self.plotRecords.setLayout(myform2)
        self.mainWidget.qscroll_plot.setWidget(self.plotRecords)
        self.mainWidget.qscroll_plot.setWidgetResizable(True)
        self.mainWidget.qscroll_plot.setFixedHeight(120)
        self.plotList = []

    def addPlot(self, ant, color=0):
        print "Adding to the plot list Antenna # %d"%(ant)

        rec = create_plot_record(ant, self.cells)
        rec['Color'].setCurrentIndex(color)
        rec['Color'].currentIndexChanged.connect(lambda state, g=rec: self.change_color(g))
        myform=self.plotRecords.layout()

        myform.addRow(rec['frame'])
        self.plotRecords.setLayout(myform)
        self.plotList += [[rec['Base'],color]]
        pass

    def updatePlotList(self):
        self.mainWidget.qcombo_plotList.clear()
        lista=sorted(os.listdir(PATH_PLOT_LIST))
        for i in lista:
            self.mainWidget.qcombo_plotList.addItem(i.split(".")[0])
        pass


    def change_color(self,r):
        for i in xrange(len(self.plotList)):
            if self.plotList[i][0] == r['Base']:
                self.plotList[i] = [r['Base'],r['Color'].currentIndex()]
                break


    def openPreadu(self, record):
        pass


    def clearPlotList(self):
        self.initPlotList()
        self.plotList = []
        print "Plot List deleted!"

    def savePlotList(self):
        if not os.path.exists(PATH_PLOT_LIST):
            os.makedirs(PATH_PLOT_LIST)
        okscrivi = True
        if os.path.isfile(PATH_PLOT_LIST+self.mainWidget.qtext_listname.text()+".list"):
            result = QtGui.QMessageBox.question(self,
                          "Confirm Overwrite...",
                          "Are you sure you want to overwrite the existing file \""+self.mainWidget.qtext_listname.text()+"\" ?",
                          QtGui.QMessageBox.Yes| QtGui.QMessageBox.No)

            if result == QtGui.QMessageBox.Yes:
                okscrivi = True
            else:
                okscrivi = False
        if okscrivi:
            with open(PATH_PLOT_LIST+self.mainWidget.qtext_listname.text()+".list","w") as f:
                print self.plotList
                for (ant,color) in self.plotList:
                    print ant,color
                    f.write(str(ant)+","+str(color)+"\n")
            print "Plot List \""+self.mainWidget.qtext_listname.text()+"\" saved!"
        self.updatePlotList()

    def loadPlotList(self):
        nomelista = easygui.fileopenbox(msg='Please select the Plot List', default=".plotlists/*.list")
        try:
            with open(nomelista, "r") as f:
                a=f.readlines()
        except:
            print "Not able to load the list file!"
            pass
        self.clearPlotList()
        for i in a:
            print i
            self.addPlot(int(i.strip().split(",")[0]), int(i.strip().split(",")[1]))

        print "Plot List loaded."

    def change_poly(self):
        if not self.switchtox:
            print self.mainWidget.cb_polx.isChecked(), self.mainWidget.cb_poly.isChecked(),
            self.switchtoy = True
            if self.mainWidget.cb_poly.isChecked():
                self.poly = True
                self.polx = False
                self.mainWidget.cb_polx.setChecked(False)
            elif not self.mainWidget.cb_polx.isChecked():
                self.poly = True
                self.mainWidget.cb_poly.setChecked(True)
            self.switchtoy = False
            print self.mainWidget.cb_polx.isChecked(),self.mainWidget.cb_poly.isChecked()

    def change_polx(self):
        if not self.switchtoy:
            print self.mainWidget.cb_polx.isChecked(), self.mainWidget.cb_poly.isChecked(),
            self.switchtox = True
            if self.mainWidget.cb_polx.isChecked():
                self.polx = True
                self.poly = False
                self.mainWidget.cb_poly.setChecked(False)
            elif not self.mainWidget.cb_poly.isChecked():
                 self.polx = True
                 self.mainWidget.cb_polx.setChecked(True)
            self.switchtox=False
            print self.mainWidget.cb_polx.isChecked(),self.mainWidget.cb_poly.isChecked()

    #def plotSpectra(self):

    def onclick(self, event):
        #print("APRITI!!!")
        if event.dblclick and not event.xdata == None:
            self.popwd = QtGui.QDialog()
            self.popw = AAVS_SNAP_Dialog()
            self.popw.setupUi(self.popwd)
            self.popwd.show()

            self.popwPlot = MiniPlots(self.popw.frame, 1, dpi=85)
            if event.button == 1:
                sel = [x for x in self.cells if ((x['East'] > event.xdata - 0.4) and (x['East'] < event.xdata + 0.4))]
                res = [x for x in sel if ((x['North'] > event.ydata - 0.4) and (x['North'] < event.ydata + 0.4))]
                if len(res) == 1:
                    board = {}
                    print "Selected antenna", int(res[0]['Base'])  # , len(TPMs)#,res[0]['East'], res[0]['North']
                    for i in range(len(self.TPMs)):
                        # for x in TPMs[i]['ANTENNE']:
                        #    print x['Base'], " ",
                        # print
                        if len([x for x in self.TPMs[i]['ANTENNE'] if int(x['Base']) == int(res[0]['Base'])]) > 0:
                            board['IP'] = self.TPMs[i]['IP']
                            board['TPM'] = self.TPMs[i]['TPM']
                            board['ANTENNE'] = [x for x in self.TPMs[i]['ANTENNE'] if int(x['Base']) == int(res[0]['Base'])]
                            # print board['ANTENNE'], board['IP']
                    if not board == {}:
                        if len(board['ANTENNE']) == 1:
                            freqs, spettro = get_raw_meas(board, meas="SPECTRA", debug=self.debug)
                            self.popwPlot.plotCurve(freqs, spettro[(int(board['ANTENNE'][0]['RX']) - 1) * 2], 0,colore='b', label="Pol X")
                            self.popwPlot.plotCurve(freqs, spettro[(int(board['ANTENNE'][0]['RX']) - 1) * 2 + 1], 0, colore='g', label="Pol Y")
                            self.popwPlot.updatePlot()
                            self.popw.qlabel_antnum.setText("Antenna Base # " + str(int(board['ANTENNE'][0]['Base'])))
                            self.popw.qlabel_hc.setText("Hybrid Cable: " + str(int(board['ANTENNE'][0]['Hybrid Cable'])))
                            self.popw.qlabel_rox.setText("Roxtec: " + str(int(board['ANTENNE'][0]['Roxtec'])))
                            self.popw.qlabel_rib.setText("Ribbon: " + str(int(board['ANTENNE'][0]['Ribbon'])))
                            self.popw.qlabel_fib.setText("Fibre: " + str(int(board['ANTENNE'][0]['Fibre'])))
                            self.popw.qlabel_col.setText("Colour: " + str(board['ANTENNE'][0]['Colour']))
                            self.popw.qlabel_tpm.setText("TPM: " + str(int(board['ANTENNE'][0]['TPM'])))
                            self.popw.qlabel_rx.setText("RX: " + str(int(board['ANTENNE'][0]['RX'])))


                elif len(res) > 2:
                    print "Search provides more than one result (found %d candidates)" % (len(res))
                else:
                    # print "Double clicked on x:%4.2f and y:%4.2f, no antenna found here!"%(event.xdata,event.ydata)
                    pass
            else:
                pass
        else:
            pass

    def load_events(self):
        self.mainWidget.button_runMap.clicked.connect(lambda: self.runMap())
        self.mainWidget.button_saveMap.clicked.connect(lambda: self.saveMap())
        self.mainWidget.qbutton_DeleteList.clicked.connect(lambda: self.clearPlotList())
        self.mainWidget.qbutton_SaveList.clicked.connect(lambda: self.savePlotList())
        self.mainWidget.qbutton_LoadList.clicked.connect(lambda: self.loadPlotList())
        self.mainWidget.cb_poly.stateChanged.connect(lambda: self.change_poly())
        self.mainWidget.cb_polx.stateChanged.connect(lambda: self.change_polx())

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(970, 560)
        self.frame = QtGui.QFrame(Dialog)
        self.frame.setGeometry(QtCore.QRect(10, 10, 950, 470))
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        Dialog.setWindowTitle("Spectra")


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-d", "--debug", action='store_true',
                      dest="debug",
                      default=False,
                      help="If set the program runs in debug mode")


    (options, args) = parser.parse_args()

    os.system("python ../config/setup.py")
    app = QtGui.QApplication(sys.argv)
    window = AAVS("aavs.ui",options.debug)

    #window.housekeeping_signal.connect(window.updateHK)
    #window.jig_pm_signal.connect(window.updateJIGpm)
    #window.antenna_test_signal.connect(window.updateAntennaTest)

    sys.exit(app.exec_())
