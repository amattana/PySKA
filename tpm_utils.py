import sys,struct,os,time,socket
sys.path.append("..\\")
sys.path.append("..\\..\\")
from PyQt4 import QtCore, QtGui
import numpy as np
from netproto.sdp_medicina import sdp_medicina as sdp_med
from struct import *

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


def cmd_ping(hostname):
	from sys import platform
	if platform == "linux" or platform == "linux2":
		# linux
		return os.system("ping -c 1 -W 1 "+hostname)
	elif platform == "win32":
		# Windows...
		return os.system("ping -n 1 -w 1 "+hostname)


def fpgaIsProgrammed(Tpm, fpga_idx):
    SM_XIL_reg = [0x50000004, 0x50000008]
    if (Tpm[SM_XIL_reg[fpga_idx]] & 0x2) == 0:
        return False
    else: 
        return True

def isPreaduOn(Tpm):
    if (Tpm[0x30000040] & 0x3) == 3:
        return True
    else:
        return False

def getTpmTemp(Tpm):
    Tpm[0x40000004] = 0x5
    Tpm[0x40000000] = 0x2118
    time.sleep(0.1)
    rd = Tpm[0x40000008]
    rd = ((rd >> 8) & 0x00FF) | ((rd << 8) & 0x1F00)
    rd = rd * 0.0625
    return rd

def getFpgaFwVersion(Tpm):
    ver_hex = hex(Tpm[0])[2:]
    ver = ver_hex[:1]+"."+ver_hex[1:3]+"."+ver_hex[3:]
    return(ver)
    
def getCpldFwVersion(Tpm):
    ver_hex = hex(Tpm[0x30000000])
    ver = ver_hex[2:-6].zfill(2)+"/"+ver_hex[-6:-4]+"/"+ver_hex[-4:-2]+" "+ver_hex[-2:]
    return(ver)

def getPLLStatus(Tpm):
    pll = Tpm.spi.rd_pll(0x508)
    return(pll)
    
def getADCStatus(Tpm):
    adc = Tpm.spi.rd_adc(0,0x56f)
    return(adc)
    
def save_raw(path,data,chan,seq):
    raw_filename = path + "input_" + str(chan).zfill(2) + "_" + str(seq-1).zfill(3) + ".bin"
    raw_file = open(raw_filename, "wb")
    raw_file.write(data)
    raw_file.close()
    return raw_filename


    
    
    
    