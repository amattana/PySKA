#!/usr/bin/env python
"""
PyQt4 Graphic User Interface for the iTPM ADU 

 
"""
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from tpm_utils import *
sys.path.append("../board")
sys.path.append("../rf_jig")
sys.path.append("../config")
sys.path.append("../repo_utils")
import tpm_preadu
import os, sys
from bsp.tpm import *
from gui_utils import *

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2016, Osservatorio di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

subrack={}
#subrack['tpmnum']     = 1
#subrack['tpmfw']      = '..\\..\\..\\bitstream\\'
#subrack['tpmchannel'] = 'ALL'
#subrack['tpmpll']     = '800'
subrack['srconfig']  = [{'ipaddr': '10.0.10.2',
                          'preadu_l': '2016-06_001_008',
                          'preadu_r': '2016-06_009_016',
                          'subrack_position': '0',
                          'serial': '1.02.01'}]

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

def tpm_obj(Dialog, tpm_config):
    tpm = {}

    tpm['TPM'] = TPM(ip=tpm_config['ipaddr'], port=tpm_config['udpport'], timeout=tpm_config['udptimeout'])

    tpm['frame_tpm'] = QtGui.QFrame(Dialog)
    tpm['frame_tpm'].setGeometry(QtCore.QRect((int(tpm_config['subrack_position'])*220)+10, 10, 201, 641))
    tpm['frame_tpm'].setAutoFillBackground(True)
    tpm['frame_tpm'].setStyleSheet(_fromUtf8("border-color: rgb(0, 0, 0);\n"
"border-top-color: rgb(0, 0, 0);"))
    tpm['frame_tpm'].setFrameShape(QtGui.QFrame.StyledPanel)
    tpm['frame_tpm'].setFrameShadow(QtGui.QFrame.Plain)
    tpm['frame_tpm'].setLineWidth(1)
    tpm['frame_tpm'].setMidLineWidth(0)

    tpm['fpga0'] = QtGui.QLabel(tpm['frame_tpm'])
    tpm['fpga0'].setEnabled(False)
    tpm['fpga0'].setGeometry(QtCore.QRect(10, 20, 171, 21))
    tpm['fpga0'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['fpga0'].setText(_translate("Dialog", "FPGA 0", None))
    tpm['fpga0'].setStyleSheet(colors('white_on_red'))

    tpm['fpga1'] = QtGui.QLabel(tpm['frame_tpm'])
    tpm['fpga1'].setEnabled(False)
    tpm['fpga1'].setGeometry(QtCore.QRect(10, 50, 171, 21))
    tpm['fpga1'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['fpga1'].setText(_translate("Dialog", "FPGA 1", None))
    tpm['fpga1'].setStyleSheet(colors('white_on_red'))

    tpm['cpld_fw'] = QtGui.QLabel(tpm['frame_tpm'])
    tpm['cpld_fw'].setEnabled(False)
    tpm['cpld_fw'].setGeometry(QtCore.QRect(10, 80, 171, 21))
    tpm['cpld_fw'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['cpld_fw'].setText(_translate("Dialog", "CPLD FW Ver: n/a ", None))

    tpm['fpga_fw'] = QtGui.QLabel(tpm['frame_tpm'])
    tpm['fpga_fw'].setEnabled(False)
    tpm['fpga_fw'].setGeometry(QtCore.QRect(10, 110, 171, 21))
    tpm['fpga_fw'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['fpga_fw'].setText(_translate("Dialog", "FPGA FW Ver: n/a ", None))

    line_1 = QtGui.QFrame(tpm['frame_tpm'])
    line_1.setGeometry(QtCore.QRect(10, 140, 171, 20))
    line_1.setFrameShape(QtGui.QFrame.HLine)
    line_1.setFrameShadow(QtGui.QFrame.Sunken)

    tpm['pll_freq'] = QtGui.QLabel(tpm['frame_tpm'])
    tpm['pll_freq'].setEnabled(False)
    tpm['pll_freq'].setGeometry(QtCore.QRect(10, 170, 171, 21))
    tpm['pll_freq'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['pll_freq'].setText(_translate("Dialog", "PLL 800 MHz", None))

    tpm['pll_lock'] = QtGui.QLabel(tpm['frame_tpm'])
    tpm['pll_lock'].setEnabled(False)
    tpm['pll_lock'].setGeometry(QtCore.QRect(10, 200, 171, 21))
    tpm['pll_lock'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['pll_lock'].setText(_translate("Dialog", "PLL Locked", None))

    tpm['pll_ref'] = QtGui.QLabel(tpm['frame_tpm'])
    tpm['pll_ref'].setEnabled(False)
    tpm['pll_ref'].setGeometry(QtCore.QRect(10, 230, 171, 21))
    tpm['pll_ref'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['pll_ref'].setText(_translate("Dialog", "Ext 10 MHz Ref", None))

    line_2 = QtGui.QFrame(tpm['frame_tpm'])
    line_2.setGeometry(QtCore.QRect(10, 260, 171, 20))
    line_2.setFrameShape(QtGui.QFrame.HLine)
    line_2.setFrameShadow(QtGui.QFrame.Sunken)

    tpm['label_preadu']= QtGui.QLabel(tpm['frame_tpm'])
    tpm['label_preadu'].setEnabled(False)
    tpm['label_preadu'].setGeometry(QtCore.QRect(10, 300, 171, 21))
    tpm['label_preadu'].setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    tpm['label_preadu'].setMouseTracking(True)
    tpm['label_preadu'].setAcceptDrops(True)
    tpm['label_preadu'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['label_preadu'].setText(_translate("Dialog", "PRE-ADU", None))
    tpm['label_preadu'].setStyleSheet(colors("white_on_red"))

    line_3 = QtGui.QFrame(tpm['frame_tpm'])
    line_3.setGeometry(QtCore.QRect(10, 350, 171, 20))
    line_3.setFrameShape(QtGui.QFrame.HLine)
    line_3.setFrameShadow(QtGui.QFrame.Sunken)

    tpm['temp'] = QtGui.QLabel(tpm['frame_tpm'])
    tpm['temp'].setEnabled(False)
    tpm['temp'].setGeometry(QtCore.QRect(10, 380, 171, 21))
    tpm['temp'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['temp'].setText(_translate("Dialog", "Temp 60 deg [C]", None))

    line_4 = QtGui.QFrame(tpm['frame_tpm'])
    line_4.setGeometry(QtCore.QRect(10, 420, 171, 20))
    line_4.setFrameShape(QtGui.QFrame.HLine)
    line_4.setFrameShadow(QtGui.QFrame.Sunken)

    tpm['connected'] = QtGui.QLabel(tpm['frame_tpm'])
    tpm['connected'].setEnabled(True)
    tpm['connected'].setGeometry(QtCore.QRect(10, 490, 171, 21))
    tpm['connected'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['connected'].setText(_translate("Dialog", "offline", None))
    tpm['connected'].setStyleSheet(colors("white_on_red"))

    tpm['serial'] = QtGui.QLabel(tpm['frame_tpm'])
    tpm['serial'].setEnabled(True)
    tpm['serial'].setGeometry(QtCore.QRect(10, 540, 171, 21))
    tpm['serial'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['serial'].setText(_translate("Dialog", "s/n: "+tpm_config['serial'], None))

    tpm['qipaddr'] = QtGui.QLabel(tpm['frame_tpm'])
    tpm['qipaddr'].setGeometry(QtCore.QRect(10, 570, 171, 21))
    tpm['qipaddr'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['qipaddr'].setText(_translate("Dialog", "IP: "+tpm_config['ipaddr'], None))
    tpm['qipaddr'].setEnabled(True)
    tpm['ipaddr'] = tpm_config['ipaddr']

    tpm['qmacaddr'] = QtGui.QLabel(tpm['frame_tpm'])
    tpm['qmacaddr'].setGeometry(QtCore.QRect(10, 600, 171, 21))
    tpm['qmacaddr'].setAlignment(QtCore.Qt.AlignCenter)
    tpm['qmacaddr'].setText(_translate("Dialog", "MAC: "+tpm_config['macaddr'], None))
    tpm['qmacaddr'].setEnabled(True)

    return tpm

'''
    tpm['button_connect'] = QtGui.QPushButton(tpm['frame_tpm'])
    tpm['button_connect'].setGeometry(QtCore.QRect(10, 600, 151, 21))
    tpm['button_connect'].setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    tpm['button_connect'].setAutoFillBackground(False)
    tpm['button_connect'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 0);\n"
"selection-background-color: rgb(0, 0, 255);\n"
"border-color: rgb(0, 0, 0);\n"
"alternate-background-color: rgb(255, 255, 0);\n"
"selection-color: rgb(255, 255, 0);"))
    tpm['button_connect'].setToolTip(_translate("Dialog", "<html><head/><body><p>Press to connet/disconnet the resource</p></body></html>", None))
    tpm['button_connect'].setText(_translate("Dialog", "Prog_Fpgas", None))

    self.qlabel_amp = QtGui.QLabel(self.qframe_tpm)
    self.qlabel_amp.setEnabled(False)
    self.qlabel_amp.setGeometry(QtCore.QRect(10, 450, 151, 21))
    self.qlabel_amp.setAlignment(QtCore.Qt.AlignCenter)
    self.qlabel_amp.setObjectName(_fromUtf8("qlabel_amp"))
    self.qlabel_power = QtGui.QLabel(self.qframe_tpm)
    self.qlabel_power.setEnabled(False)
    self.qlabel_power.setGeometry(QtCore.QRect(10, 480, 151, 21))
    self.qlabel_power.setAlignment(QtCore.Qt.AlignCenter)
    self.qlabel_power.setObjectName(_fromUtf8("qlabel_power"))
    self.qlabel_volt = QtGui.QLabel(self.qframe_tpm)
    self.qlabel_volt.setEnabled(False)
    self.qlabel_volt.setGeometry(QtCore.QRect(10, 420, 151, 21))
    self.qlabel_volt.setAlignment(QtCore.Qt.AlignCenter)
    self.qlabel_volt.setObjectName(_fromUtf8("qlabel_volt"))
    self.qlabel_amp.setText(_translate("Dialog", "8.10 Amp", None))
    self.qlabel_power.setText(_translate("Dialog", "120 Watt", None))
    self.qlabel_volt.setText(_translate("Dialog", "16.0 Volt", None))
'''

class adu_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.resize(self.tpm_num*220, 710)
        Dialog.setAutoFillBackground(False)
        Dialog.setWindowTitle(_translate("Dialog", "TPM_Subrack", None))
        
        self.tpms = []
        for tpm_index in xrange(self.tpm_num):
            self.tpms += [tpm_obj(Dialog, self.subrack['srconfig'][tpm_index])]  
            
        self.button_update = QtGui.QPushButton(Dialog)
        self.button_update.setGeometry(QtCore.QRect(((self.tpm_num*220)/2)-45, 665, 90, 31))
        self.button_update.setText(_translate("tpm_conf", "UPDATE", None))
        self.button_update.clicked.connect(lambda: self.updateUI())
        
        self.updateUI()

    def slotUpdate(self):
        self.updateUI()
        
        
    def updateUI(self):
        for tpm_index in xrange(self.tpm_num):
            if cmd_ping(self.tpms[tpm_index]['ipaddr']) == 0:
                self.tpms[tpm_index]['connected'].setStyleSheet(colors("black_on_green"))    
                self.tpms[tpm_index]['connected'].setText(_translate("Dialog", "online", None))
                self.tpms[tpm_index]['label_preadu'].setEnabled(True)
                self.tpms[tpm_index]['cpld_fw'].setEnabled(True)
                self.tpms[tpm_index]['cpld_fw'].setText(_translate("Dialog", "CPLD: "+getCpldFwVersion(self.tpms[tpm_index]['TPM']), None))

                if fpgaIsProgrammed(self.tpms[tpm_index]['TPM'], 0):
                    self.tpms[tpm_index]['fpga0'].setStyleSheet(colors('black_on_green'))
                    self.tpms[tpm_index]['fpga_fw'].setEnabled(True)
                    self.tpms[tpm_index]['fpga_fw'].setText(_translate("Dialog", "FPGA: "+getFpgaFwVersion(self.tpms[tpm_index]['TPM']), None))
                else:
                    self.tpms[tpm_index]['fpga0'].setStyleSheet(colors('white_on_red'))
                    self.tpms[tpm_index]['fpga_fw'].setText(_translate("Dialog", "FPGA Fw Ver: n/a", None))
                if fpgaIsProgrammed(self.tpms[tpm_index]['TPM'], 1):
                    self.tpms[tpm_index]['fpga1'].setStyleSheet(colors('black_on_green'))
                else:
                    self.tpms[tpm_index]['fpga1'].setStyleSheet(colors('white_on_red'))
                if isPreaduOn(self.tpms[tpm_index]['TPM']):
                    self.tpms[tpm_index]['label_preadu'].setStyleSheet(colors('black_on_green'))
                    self.tpms[tpm_index]['label_preadu'].setEnabled(True)
                else:
                    self.tpms[tpm_index]['label_preadu'].setStyleSheet(colors('white_on_red'))
                    self.tpms[tpm_index]['label_preadu'].setEnabled(True)
                # Temperature
                self.tpms[tpm_index]['temp'].setEnabled(True)
                temp=getTpmTemp(self.tpms[tpm_index]['TPM'])
                self.tpms[tpm_index]['temp'].setText(_translate("Dialog", "Temp "+str("%3.1f"%(temp))+" deg. [C]", None))
                if temp < 65:
                    self.tpms[tpm_index]['temp'].setStyleSheet(colors("black_on_green"))
                elif temp < 75:
                    self.tpms[tpm_index]['temp'].setStyleSheet(colors("black_on_yellow"))
                else:
                    self.tpms[tpm_index]['temp'].setStyleSheet(colors("white_on_red"))
            else:
                self.tpms[tpm_index]['connected'].setStyleSheet(colors("white_on_red"))    
                self.tpms[tpm_index]['connected'].setText(_translate("Dialog", "offline", None))
                self.tpms[tpm_index]['label_preadu'].setEnabled(False)
                self.tpms[tpm_index]['cpld_fw'].setEnabled(False)
                self.tpms[tpm_index]['fpga_fw'].setEnabled(False)
                
            

class tpm_adu_gui(QtGui.QMainWindow, adu_Dialog):

    # custom slot
    def mymethod(self, tpm):
        self.tpms[tpm]['serial'].setText('Hello World')
        #self.textFieldExample.clear()

    def open_preadu_conf(self, tpm):
        if self.tpms[tpm]['label_preadu'].isEnabled():
            self.tpms[tpm]['preadu'] = tpm_preadu.preaduWindow(self.tpms[tpm]['TPM'], self.subrack['srconfig'][tpm])
            self.tpms[tpm]['preadu'].show()

    def __init__(self, subrack):
        QtGui.QMainWindow.__init__(self)
        self.subrack = subrack 
        self.tpm_num = len(self.subrack['srconfig'])
        # set up User Interface (widgets, layout...)
        self.setupUi(self)

        for tpm in xrange(self.tpm_num):
            # custom slots connections
            #self.tpms[tpm]['button_connect'].clicked.connect(lambda state, itpm=tpm: self.mymethod(itpm)) # signal/slot connection
            # Making clickable non clickable object!
            clickable(self.tpms[tpm]['label_preadu']).connect(lambda itpm=tpm: self.open_preadu_conf(itpm)) # signal/slot connection


# Main entry to program.  Sets up the main app and create a new window.
def main(argv):

    # create Qt application
    app = QtGui.QApplication(argv,True)

    # create main window
    wnd = tpm_adu_gui(subrack) # classname
    wnd.show()

    # Connect signal for app finish
    app.connect(app, QtCore.SIGNAL("lastWindowClosed()"), app, QtCore.SLOT("quit()"))

    # Start the app up
    sys.exit(app.exec_())


if __name__ == "__main__":
    main(sys.argv)



