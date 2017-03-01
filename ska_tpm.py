#!/usr/bin/env python
"""
PyQt4 Graphic User Interface for the SKA iTPM SubRack 

 
"""
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os,sys,glob
sys.path.append("..\\")
sys.path.append("..\\..\\")
sys.path.append("../board/netproto")
import tpm_adu 
import xml.etree.ElementTree as ET
from gui_utils import *

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2016, Osservatorio di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

config_file='ska_tpm.xml'

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


class Ui_tpm_conf(object):
    def setupUi(self, tpm_conf):
        tpm_conf.setObjectName(_fromUtf8("tpm_conf"))
        tpm_conf.resize(630, 430)
        tpm_conf.setWindowTitle(_translate("tpm_conf", "SKA - TPM SubRack Setup", None))
        #tpm_conf.setStyleSheet("background-color: rgb(255, 255, 255)")

        self.pic_ska = QtGui.QLabel(tpm_conf)
        self.pic_ska.setGeometry(30, 20, 575, 200)
        self.pic_ska.setPixmap(QtGui.QPixmap(os.getcwd() + "/pic/ska_inaf_logo.jpg"))

        self.label_profiles = QtGui.QLabel(tpm_conf)
        self.label_profiles.setGeometry(QtCore.QRect(30, 230, 131, 31))
        self.label_profiles.setText(_translate("tpm_conf", "Subrack Profile:", None))

        self.cb_profiles = QtGui.QComboBox(tpm_conf)
        self.cb_profiles.setGeometry(QtCore.QRect(170, 230, 435, 31))
        self.cb_profiles.addItems(glob.glob("*xml"))
        self.cb_profiles.currentIndexChanged.connect(self.checkSubrackProfile)

        self.label_fpga_fw = QtGui.QLabel(tpm_conf)
        self.label_fpga_fw.setGeometry(QtCore.QRect(30, 280, 131, 31))
        self.label_fpga_fw.setText(_translate("tpm_conf", "FPGAs Firmware:", None))

        self.cb_fpga_fw = QtGui.QComboBox(tpm_conf)
        self.cb_fpga_fw.setGeometry(QtCore.QRect(170, 280, 435, 31))

        self.label_pll_clk = QtGui.QLabel(tpm_conf)
        self.label_pll_clk.setGeometry(QtCore.QRect(30, 380, 131, 31))
        self.label_pll_clk.setText(_translate("tpm_conf", "PLL Clock (MSPS):", None))

        self.cb_pll_clk = QtGui.QComboBox(tpm_conf)
        self.cb_pll_clk.setGeometry(QtCore.QRect(170, 380, 81, 31))
        self.cb_pll_clk.addItems(["800", "700", "1000"])

        self.label_input = QtGui.QLabel(tpm_conf)
        self.label_input.setGeometry(QtCore.QRect(30, 330, 141, 31))
        self.label_input.setText(_translate("tpm_conf", "Input to Download:", None))

        self.cb_input = QtGui.QComboBox(tpm_conf)
        self.cb_input.setGeometry(QtCore.QRect(170, 330, 435, 31))
        self.cb_input.addItems(["ALL", "0,8,16,24",])
        self.cb_input.setCurrentIndex(0)

        self.label_tpm_num = QtGui.QLabel(tpm_conf)
        self.label_tpm_num.setGeometry(QtCore.QRect(280, 380, 200, 31))
        self.label_tpm_num.setText(_translate("tpm_conf", "Number of TPMs: -", None))

        #self.label_tpm_num = QtGui.QComboBox(tpm_conf)
        #self.cb_tpm_num.setGeometry(QtCore.QRect(400, 380, 81, 31))
        #self.cb_tpm_num.addItems(["1", "2", "3", "4", "5", "6", "7", "8"])

        self.button_start = QtGui.QPushButton(tpm_conf)
        self.button_start.setGeometry(QtCore.QRect(510, 380, 94, 31))
        self.button_start.setText(_translate("tpm_conf", "Start", None))

        self.cb_fpga_fw.addItems(sorted(glob.glob("..\\..\\bitstream\\*.bit")))
        self.button_start.clicked.connect(lambda: self.action_start())

    def action_start(self):
        subrack={}
        #subrack['tpmnum']     = int(str(self.cb_tpm_num.currentText()))
        #subrack['tpmfw']      = str(self.cb_fpga_fw.currentText())
        #subrack['tpmchannel'] = str(self.cb_input.currentText())
        #subrack['tpmpll']     = str(self.cb_pll_clk.currentText())
        subrack['srconfig']   = xmlparser(self.cb_profiles.currentText())
        self.adu_gui = tpm_adu.tpm_adu_gui(subrack)
        self.adu_gui.show()

    def checkSubrackProfile(self):
        self.label_tpm_num.setText("Number of TPM in the Subrack: "+str(len(xmlparser(self.cb_profiles.currentText()))))

        
class tpm_conf(QtGui.QMainWindow, Ui_tpm_conf):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)

# Main entry to program.  Sets up the main app and create a new window.
def main(argv):

    # create Qt application
    app = QtGui.QApplication(argv,True)

    # create main window
    wnd = tpm_conf() # classname
    wnd.show()

    # Connect signal for app finish
    app.connect(app, QtCore.SIGNAL("lastWindowClosed()"), app, QtCore.SLOT("quit()"))

    # Start the app up
    sys.exit(app.exec_())


if __name__ == "__main__":
    main(sys.argv)



