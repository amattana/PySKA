#!/usr/bin/env python
"""
PyQt4 Graphic User Interface for the iTPM Pre-ADU 

 
"""
import sys,struct,time
sys.path.append("..\\")
sys.path.append("..\\..\\")
from PyQt4 import QtCore, QtGui
from tpm_utils import *
from gui_utils import *

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2016, Osservatorio di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

try:
    # try ping!
    #from tpm_read_preadu import read_preadu_regs
    #from tpm_write_preadu import write_preadu_regs
    DEBUG=0
except:
    #print "Not able to load TPM libraries, using debug mode"
    DEBUG=1


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

CHANNELS=32

LABEL_WIDTH  = 23
LABEL_HEIGHT = 21
TEXT_WIDTH   = 50
TEXT_HEIGHT  = 22
FLAG_WIDTH   = 40
FLAG_HEIGHT  = 21

TABLE_HSPACE = 430
TABLE_VSPACE = 30

DIALOG_WIDTH  = 850
DIALOG_HEIGHT = 720

SIGNALS_MAP_FILENAME = "signals_map.txt"

tpm_config  = {'ipaddr': '10.0.10.2',
                'preadu_l': '2016-06_001_008',
                'preadu_r': '2016-06_009_016',
                'subrack_position': '0',
                'serial': '1.02.01'}

# This creates the input label (eg: for input 15 -> "15:") 
def create_label(Dialog, x, y, text):
    label = QtGui.QLabel(Dialog)
    label.setGeometry(QtCore.QRect(x, y, LABEL_WIDTH, LABEL_HEIGHT))
    label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
    label.setText(_translate("Dialog", text, None))
    return label

# This creates the text lineEdit for the attenuation values 
def create_text(Dialog, x, y, text):
    qtext = QtGui.QLineEdit(Dialog)
    qtext.setGeometry(QtCore.QRect(x, y, TEXT_WIDTH, TEXT_HEIGHT))
    qtext.setAlignment(QtCore.Qt.AlignCenter)
    qtext.setText(_translate("Dialog", text, None))
    return qtext

def update_text(qtext, text):
    qtext.setText(_translate("Dialog", text, None))

# This creates the flags "hi" and "lo" using a background color
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

# This creates the buttons "-" and "+" 
def create_button(Dialog, x, y, text):
    qbutton = QtGui.QPushButton(Dialog)
    qbutton.setGeometry(QtCore.QRect(x, y, 30, 21))
    qbutton.setText(_translate("Dialog", text, None))
    return qbutton



def update_flag(record, val):
    #print val,
    if (val&0b100)==4: # Low Band
        #print "LOW", 
        record['hi'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 0);"))
        record['lo'].setStyleSheet(_fromUtf8("background-color: rgb(0, 170, 0);"))
    elif (val&0b10)==2:  # High Band
        #print "HIGH", 
        record['lo'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 0);"))
        record['hi'].setStyleSheet(_fromUtf8("background-color: rgb(0, 170, 0);"))
    else:
        print "Found invalid configuration for Preadu-Filters: ", bin(val) 
        record['lo'].setStyleSheet(_fromUtf8("background-color: rgb(0, 0, 0);"))
        record['hi'].setStyleSheet(_fromUtf8("background-color: rgb(0, 0, 0);"))
    if (val&1)==0:   # 50 Ohm
        #print "50Ohm", 
        record['rf'].setStyleSheet(_fromUtf8("background-color: rgb(220, 40, 40);"))
    else:
        record['rf'].setStyleSheet(_fromUtf8("background-color: rgb(0, 170, 0);"))

def create_record(Dialog, rf_map):
    rec = {}
    idx = int(rf_map[0])
    rec['reg_val'] = 0
    rec['label'] = create_label(Dialog, 20+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), rf_map[0]+":")
    rec['value'] = create_label(Dialog, 45+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "0")
    rec['text'] = create_text(Dialog,  80+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "0")
    rec['minus'] = create_button(Dialog,  140+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "-")
    rec['plus'] = create_button(Dialog,  170+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "+")
    rec['lo'] = create_flag(Dialog, 210+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "green", "LO")
    rec['hi'] = create_flag(Dialog, 260+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "yellow", "HI")
    rec['rf'] = create_flag(Dialog, 310+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "green", rf_map[1])
    rec['of'] = create_flag(Dialog, 360+(((idx & 8)>>3)*TABLE_HSPACE), 90+((idx & 7)*TABLE_VSPACE)+(((idx & 16)>>4)*280), "cyan", rf_map[2])
    return rec

def spi_bit_reverse(n):
    return int("%d"%(int('{:08b}'.format(n)[::-1], 2)))

def font_bold():
    font = QtGui.QFont()
    font.setBold(True)
    font.setWeight(75)
    return font
def font_normal():
    font = QtGui.QFont()
    return font


def read_routing_table():
    mappa=[]
    f_map = open(SIGNALS_MAP_FILENAME)
    input_list=f_map.readlines()
    for i in xrange(CHANNELS):
        mappa += [[input_list[i].split(":")[0], input_list[i].split(":")[1].split()[0], input_list[i].split(":")[1].split()[1]]]
    f_map.close()
    return mappa


class preadu_Dialog(object):

    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(DIALOG_WIDTH, DIALOG_HEIGHT)
        Dialog.setWindowTitle(_translate("Dialog", "Pre-ADU Configuration for TPM: s/n "+self.tpm_config['serial']+"  (IP: "+self.tpm_config['ipaddr']+")", None))

        self.inputs=CHANNELS
        if DEBUG==0:
            print "Read pre-ADU Registers..."
            self.preadu_val=read_preadu_regs(self.Tpm)
        else:
            self.preadu_val=[0xa0a0a0a0,0xa0a0a0a0,0xa0a0a0a0,0xa0a0a0a0,0xa0a0a0a0,0xa0a0a0a0,0xa0a0a0a0,0xa0a0a0a0]
        self.chan_remap=[  
                          19, 18, 17, 16, 23, 22, 21, 20,   # ok
                            12, 13, 14, 15, 8,  9, 10, 11,  # ok
                        27, 26, 25, 24, 31, 30, 29, 28,     # ok
                         4,  5,  6,  7, 0,  1,  2,  3,      # ok
                         ]

        self.spi_remap =[
                          8, 9, 10, 11, 12, 13, 14, 15,      # ok
                           24, 25, 26, 27, 28, 29, 30, 31,   # ok
                          23, 22, 21, 20,19, 18, 17, 16,     # ok
                          7, 6, 5, 4, 3, 2, 1, 0             # ok
                         ]

        self.label_top = QtGui.QLabel(Dialog)
        self.label_top.setGeometry(QtCore.QRect(20, 20, 380, 21))
        self.label_top.setAlignment(QtCore.Qt.AlignCenter)
        self.label_top.setText(_translate("Dialog", "PRE-ADU BOTTOM (LEFT):  s/n "+self.tpm_config['preadu_l'], None))

        self.label_bottom = QtGui.QLabel(Dialog)
        self.label_bottom.setGeometry(QtCore.QRect(450, 20, 380, 21))
        self.label_bottom.setAlignment(QtCore.Qt.AlignCenter)
        self.label_bottom.setText(_translate("Dialog", "PRE-ADU TOP (RIGHT):  s/n "+self.tpm_config['preadu_r'], None))

        table_names = "  # Code     Attenuation               Bands             Rx      Fibre"
        self.label_legend_1 = QtGui.QLabel(Dialog)
        self.label_legend_1.setGeometry(QtCore.QRect(20, 60, 500, 31))
        self.label_legend_1.setText(_translate("Dialog", table_names, None))
        self.label_legend_2 = QtGui.QLabel(Dialog)
        self.label_legend_2.setGeometry(QtCore.QRect(450, 60, 500, 31))
        self.label_legend_2.setText(_translate("Dialog", table_names, None))
        self.label_legend_3 = QtGui.QLabel(Dialog)
        self.label_legend_3.setGeometry(QtCore.QRect(20, 340, 500, 31))
        self.label_legend_3.setText(_translate("Dialog", table_names, None))
        self.label_legend_4 = QtGui.QLabel(Dialog)
        self.label_legend_4.setGeometry(QtCore.QRect(450, 340, 500, 31))
        self.label_legend_4.setText(_translate("Dialog", table_names, None))


        self.frame_all = QtGui.QFrame(Dialog)
        self.frame_all.setGeometry(QtCore.QRect(10, 665, 510, 40))
        self.frame_all.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame_all.setFrameShadow(QtGui.QFrame.Raised)
        self.label_all = QtGui.QLabel(self.frame_all)
        self.label_all.setGeometry(QtCore.QRect(5, 10, 35, 21))
        self.label_all.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_all.setText(_translate("Dialog", "ALL:", None))
        self.comboBox = QtGui.QComboBox(self.frame_all)
        self.comboBox.setGeometry(QtCore.QRect(50, 5, 50, 31))
        self.comboBox.addItems([ "0",  "1",  "2",  "3",  "4",  "5",  "6",  "7",  "8",  "9",
                                "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
                                "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
                                "30", "31"])
        self.comboBox.setCurrentIndex(0)
        self.comboBox.currentIndexChanged.connect(self.selection_change)

        self.button_dicrease = QtGui.QPushButton(self.frame_all)
        self.button_dicrease.setGeometry(QtCore.QRect(110, 5, 90, 31))
        self.button_increase = QtGui.QPushButton(self.frame_all)
        self.button_increase.setGeometry(QtCore.QRect(210, 5, 90, 31))
        self.button_rfon = QtGui.QPushButton(self.frame_all)
        self.button_rfon.setGeometry(QtCore.QRect(310, 5, 90, 31))
        self.button_rfoff = QtGui.QPushButton(self.frame_all)
        self.button_rfoff.setGeometry(QtCore.QRect(410, 5, 90, 31))
        self.button_discard = QtGui.QPushButton(Dialog)
        self.button_discard.setGeometry(QtCore.QRect(540, 670, 90, 31))
        self.button_close = QtGui.QPushButton(Dialog)
        self.button_close.setGeometry(QtCore.QRect(640, 670, 90, 31))
        self.button_apply = QtGui.QPushButton(Dialog)
        self.button_apply.setGeometry(QtCore.QRect(740, 670, 90, 31))

        self.button_discard.setText(_translate("preadu_conf", "Discard", None))
        self.button_dicrease.setText(_translate("preadu_conf", "Decrease", None))
        self.button_increase.setText(_translate("preadu_conf", "Increase", None))
        self.button_rfon.setText(_translate("preadu_conf", "Set RF", None))
        self.button_rfoff.setText(_translate("preadu_conf", "Set 50 Ohm", None))
        self.button_close.setText(_translate("preadu_conf", "Close", None))
        self.button_apply.setText(_translate("preadu_conf", "Apply", None))

        rf_map = read_routing_table()
        self.records=[]
        for i in xrange(self.inputs):
            self.records += [create_record(Dialog, rf_map[i])]


        self.label_comments = QtGui.QLabel(Dialog)
        self.label_comments.setGeometry(QtCore.QRect(20, 630, DIALOG_WIDTH-20, 21))
        self.label_comments.setAlignment(QtCore.Qt.AlignCenter)
        self.label_comments.setText(_translate("Dialog", "Pre-ADU configuration for TPM:  s/n "+self.tpm_config['serial']+"   (IP: "+self.tpm_config['ipaddr']+")", None))

        self.connections()

        self.updateForm(self.preadu_val)


    def connections(self):

        self.button_discard.clicked.connect(lambda: self.updateForm(self.preadu_val))
        self.button_dicrease.clicked.connect(lambda: self.decreaseAll())
        self.button_increase.clicked.connect(lambda: self.increaseAll())
        self.button_rfon.clicked.connect(lambda: self.rfonAll())
        self.button_rfoff.clicked.connect(lambda: self.rfoffAll())
        self.button_close.clicked.connect(lambda: self.closeDialog())
        self.button_apply.clicked.connect(lambda: self.program())
        for group in xrange(self.inputs): 
            self.records[group]['minus'].clicked.connect(lambda state, g=group: self.action_minus(g))
            self.records[group]['plus'].clicked.connect(lambda  state, g=group:  self.action_plus(g))
            # Making clickable non clickable object!
            clickable(self.records[group]['lo']).connect(self.set_lo) # signal/slot connection for flag "lo"
            clickable(self.records[group]['hi']).connect(self.set_hi) # signal/slot connection for flag "hi"
            clickable(self.records[group]['rf']).connect(lambda  g=group:  self.set_rf(g)) # signal/slot connection for flag "rf"


    def updateForm(self, a):
        t=struct.pack('<8L',a[3],a[2],a[1],a[0],a[7],a[6],a[5],a[4])
        byte_val=struct.unpack('32B',t)
        for num in xrange(self.inputs):
            register_value=spi_bit_reverse(byte_val[self.chan_remap[num]]) 
            self.records[num]['reg_val']=register_value
            self.records[num]['value'].setText(_translate("Dialog", str(hex(register_value))[2:], None))
            update_text(self.records[num]['text'], str((register_value & 0b11111000)>>3))
            update_flag(self.records[num], (register_value & 0b111) )
            self.records[num]['value'].setFont(font_normal())
            
    def set_hi(self):
        for num in xrange(self.inputs): 
            self.records[num]['lo'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 0);"))
            self.records[num]['hi'].setStyleSheet(_fromUtf8("background-color: rgb(0, 170, 0);"))
            conf_value=('0x'+self.records[num]['value'].text()).toInt(16)[0] & 0b11111011
            conf_value=conf_value | 0b10
            self.records[num]['value'].setFont(font_bold())
            self.records[num]['value'].setText(_translate("Dialog", hex(conf_value)[2:], None))
            update_flag(self.records[num], (conf_value & 0b111) )

    def set_lo(self):
        for num in xrange(self.inputs): 
            self.records[num]['hi'].setStyleSheet(_fromUtf8("background-color: rgb(255, 255, 0);"))
            self.records[num]['lo'].setStyleSheet(_fromUtf8("background-color: rgb(0, 170, 0);"))
            conf_value=('0x'+self.records[num]['value'].text()).toInt(16)[0] & 0b11111101
            conf_value=conf_value | 0b100
            self.records[num]['value'].setFont(font_bold())
            self.records[num]['value'].setText(_translate("Dialog", hex(conf_value)[2:], None))
            update_flag(self.records[num], (conf_value & 0b111) )

    def set_rf(self, num):
        conf_value=('0x'+self.records[num]['value'].text()).toInt(16)[0]
        if (conf_value & 1) == 1:
            conf_value=conf_value & 0b11111110
            self.records[num]['value'].setFont(font_bold())
            self.records[num]['value'].setText(_translate("Dialog", hex(conf_value)[2:], None))
            update_flag(self.records[num], (conf_value & 0b111) )
        else:
            conf_value=conf_value | 1
            self.records[num]['value'].setFont(font_bold())
            self.records[num]['value'].setText(_translate("Dialog", hex(conf_value)[2:], None))
            update_flag(self.records[num], (conf_value & 0b111) )
            
    def action_plus(self, num):
        valore=int(self.records[num]['text'].text())+1
        #print "Valore: ", valore
        if valore>31:
            valore=31
        config_value=('0x'+self.records[num]['value'].text()).toInt(16)[0] & 0b111
        self.records[num]['value'].setFont(font_bold())
        self.records[num]['value'].setText(_translate("Dialog", hex((valore<<3) + config_value)[2:], None))
        self.records[num]['text'].setText(_translate("Dialog", str(valore), None))
        
    def action_minus(self, num):
        valore=int(self.records[num]['text'].text())-1
        if valore<0:
            valore=0
        config_value=('0x'+self.records[num]['value'].text()).toInt(16)[0] & 0b111
        self.records[num]['value'].setFont(font_bold())
        self.records[num]['value'].setText(_translate("Dialog", hex((valore<<3) + config_value)[2:], None))
        self.records[num]['text'].setText(_translate("Dialog", str(valore), None))
        
    def action_rfoff(self, num):
        conf_value=('0x'+self.records[num]['value'].text()).toInt(16)[0] & 0b11111110
        self.records[num]['value'].setFont(font_bold())
        self.records[num]['value'].setText(_translate("Dialog", hex(conf_value)[2:], None))
        update_flag(self.records[num], (conf_value & 0b111) )
        
    def action_rfon(self, num):
        conf_value=('0x'+self.records[num]['value'].text()).toInt(16)[0] | 1
        self.records[num]['value'].setFont(font_bold())
        self.records[num]['value'].setText(_translate("Dialog", hex(conf_value)[2:], None))
        update_flag(self.records[num], (conf_value & 0b111) )
        
    def decreaseAll(self):
        for i in xrange(self.inputs):
            self.action_minus(i)

    def increaseAll(self):
        for i in xrange(self.inputs):
            self.action_plus(i)

    def rfoffAll(self):
        for i in xrange(self.inputs):
            self.action_rfoff(i)

    def rfonAll(self):
        for i in xrange(self.inputs):
            self.action_rfon(i)

    def selection_change(self,valore):
        for num in xrange(self.inputs):
            config_value=('0x'+self.records[num]['value'].text()).toInt(16)[0] & 0b111
            self.records[num]['value'].setFont(font_bold())
            self.records[num]['value'].setText(_translate("Dialog", hex((valore<<3) + config_value)[2:], None))
            self.records[num]['text'].setText(_translate("Dialog", str(valore), None))

    def closeDialog(self):
        self.close()
            
    def program(self):
        conf_values=''
        for num in xrange(self.inputs):
            channel_val=spi_bit_reverse(('0x'+self.records[self.spi_remap[num]]['value'].text()).toInt(16)[0])
            conf_values += struct.pack('B',channel_val)
        conf_str = struct.unpack('8I',conf_values)
        if DEBUG==0:
            read_back=write_preadu_regs(self.Tpm, conf_str)
        else:
            print "Old configuration: ", self.preadu_val
            print "Programming TPM with: ", conf_str
            read_back=conf_str
            print "Read back:", read_back
        self.preadu_val=read_back
        self.updateForm(self.preadu_val)
        #print


class preaduWindow(QtGui.QMainWindow, preadu_Dialog):
    def __init__(self, Tpm, tpm_config):
        QtGui.QMainWindow.__init__(self)
        # set up User Interface (widgets, layout...)
        self.Tpm=Tpm
        self.tpm_config=tpm_config
        self.setupUi(self)


# Main entry to program.  Sets up the main app and create a new window.
def main(argv):

    # create Qt application
    app = QtGui.QApplication(argv,True)

    # create main window
    wnd = preaduWindow(tpm_config) # classname
    wnd.show()

    # Connect signal for app finish
    app.connect(app, QtCore.SIGNAL("lastWindowClosed()"), app, QtCore.SLOT("quit()"))

    # Start the app up
    sys.exit(app.exec_())


if __name__ == "__main__":
    main(sys.argv)





