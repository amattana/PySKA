#!/usr/bin/env python
from PyQt4 import QtCore, QtGui, uic
import sys, os, socket

sys.path.append("../board")
sys.path.append("../rf_jig")
sys.path.append("../config")
sys.path.append("../repo_utils")
# sys.path.append("../board/pyska")
from tpm_utils import *
import tpm_preadu
# from ska_tpm import xmlparser
# from jig_adu_test import *
from bsp.tpm import *
# import config.manager as config_man
import manager as config_man
from netproto.sdp_medicina import sdp_medicina as sdp_med
import subprocess

DEVNULL = open(os.devnull, 'w')

import sys, easygui, datetime
# from qt_rf_jig_utils import *
from gui_utils import *
from rf_jig import *
from rfjig_bsp import *
from ip_scan import *

# try:
#     from HP6033A import VISAHP6033A
# except:
#     print "Couldn't import module pyvisa and Power Supply HP6033A"
#     pass


# Matplotlib stuff
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Other stuff
import numpy as np
import struct

# import multiprocessing
from threading import Thread

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

PL_WIDTH = 250
PL_HEIGHT = 130


def get_adu_temp(jig_adu):
    a = jig_adu.value
    print "pippo"


def imposta_filtro(jig, freqset):
    f = 0
    # print "Imposta filtri: ", f, len(NAME_FILTER)
    while f < len(NAME_FILTER):
        # print f, freqset, NAME_FILTER[f][2], NAME_FILTER[f][3]
        if freqset / 1000000. > NAME_FILTER[f][2] and freqset / 1000000. < NAME_FILTER[f][3]:
            break
        f = f + 1
    # print "F=", f
    jig.set_filter(NAME_FILTER[f][1])
    return str(NAME_FILTER[f][2]) + "-" + str(NAME_FILTER[f][3]) + " MHz"


def create_pl(Dialog, x, y):
    wdg = QtGui.QWidget(Dialog)
    wdg.setGeometry(QtCore.QRect(x, y, PL_WIDTH, PL_HEIGHT))
    pl = MiniPlot(wdg)
    pl.plotCurve([0, 1, 2, 3, 4, 5, 6, 7], [0, 1, 2, 1, 0, -1, -2, -1], yAxisRange=[-3, 3])
    return pl


def create_label(Dialog, x, y, text):
    label = QtGui.QLabel(Dialog)
    label.setGeometry(QtCore.QRect(x, y, 90, 30))
    label.setAlignment(QtCore.Qt.AlignHCenter)
    label.setText(text)
    label.setFont(QtGui.QFont("Ubuntu", 18, QtGui.QFont.Bold))
    label.setFrameShape(QtGui.QFrame.Box)
    label.show()
    return label


class iTPM(QtGui.QMainWindow):
    """ Main UI Window class """

    # Signal for Slots
    housekeeping_signal = QtCore.pyqtSignal()
    jig_pm_signal = QtCore.pyqtSignal()
    antenna_test_signal = QtCore.pyqtSignal()

    def __init__(self, uiFile):
        """ Initialise main window """
        super(iTPM, self).__init__()

        # Load window file
        self.mainWidget = uic.loadUi(uiFile)
        self.setCentralWidget(self.mainWidget)
        self.setWindowTitle("SKA AAVS1 iTPM PERFORMANCE TESTs")
        self.resize(1148, 749)

        self.pic_ska = QtGui.QLabel(self.mainWidget.qtab_conf)
        self.pic_ska.setGeometry(30, 450, 480, 200)
        self.pic_ska.setPixmap(QtGui.QPixmap(os.getcwd() + "/pic/ska_inaf_logo2.jpg"))
        self.mainWidget.qframe_ant_rms.hide()

        self.show()
        self.board_fast_rate = True
        self.board_ip = "10.0.10.2"

        self.sample_rate = 800
        self.adu_input = "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31"
        self.frequenze = []
        self.powered = False
        self.ready = False
        self.groupAntennaPlot = [[0, 1, 2, 3, 4, 5, 6, 7], [8, 9, 10, 11, 12, 13, 14, 15],
                                 [16, 17, 18, 19, 20, 21, 22, 23], [24, 25, 26, 27, 28, 29, 30, 31]]

        self.stopThreads = False
        self.goThread = True
        self.haltThread = False
        self.process_housekeeping = Thread(target=self.read_hk)
        self.temperatura = -100
        self.haltThreadTemp = True

        self.tpm_config = xmlparser("lab_1_tpm.xml")
        # self.mainWidget.qtext_adu_ip.setText(self.tpm_config[0]['ipaddr'])
        self.jig = None
        self.preadu = None

        self.connected = False
        self.matlabPlotACQ = MatplotlibPlot(self.mainWidget.plotWidgetACQ)

        self.RMSbarPlot = BarPlot(self.mainWidget.plotWidgetBar)
        self.RMSChartPlot = ChartPlot(self.mainWidget.plotWidgetChart)
        self.miniPlotsFour = MiniPlots(self.mainWidget.plotWidgetAntFour, 4)
        self.miniPlotsOne = MiniPlots(self.mainWidget.plotWidgetAntOne, 1)
        self.miniPlots = MiniPlots(self.mainWidget.plotWidgetAnt, 16)
        self.ant_test_Thread = False
        self.ant_test_enabled = False
        self.process_antenna_test = Thread(target=self.snap_antenna)
        # self.process_antenna_test.start()
        self.create_ant_table()
        self.antenna_test_acq_num = 0
        self.antenna_test_avgnum = 4
        self.dati = 0
        self.adu_rms = 0
        self.volt_rms = 0
        self.power_adc = 0
        self.power_rf = 0

        self.adu_rms_buffer = np.array(32*1200)
        self.adu_rms_buffer[:] = np.nan

        Fs = 400
        f = 10
        sample = 400
        x = np.arange(sample)
        y = np.sin(2 * np.pi * f * x / Fs)

        self.spettro = [y] * 16
        self.freqs = x
        self.data = 0
        self.spettro_mediato = self.spettro
        self.averaged_spectra = self.spettro
        self.averaged_freqs = self.spettro

        # print len(self.spettro[0]),len(self.freqs)
        # self.miniPlots.plotCurve(self.freqs, (self.spettro[0]*10)-50, 1)
        # self.miniPlots.updatePlot()
        # self.miniPlotsFour.plotCurve(self.freqs, (self.spettro[0]*10)-50, 1)
        # self.miniPlotsFour.updatePlot()
        self.mainWidget.plotWidgetAntFour.hide()
        self.mainWidget.plotWidgetAntOne.hide()
        self.mainWidget.plotWidgetBar.hide()
        self.mainWidget.plotWidgetChart.hide()
        self.mainWidget.plotWidgetAnt.show()
        self.xAxisRange = [0, 400]
        self.yAxisRange = [-100, 0]

        self.load_events()
        time.sleep(1)
        # self.select_power_supply()

    def load_events(self):
        clickable(self.mainWidget.qtext_adu_fw).connect(lambda: self.select_fpga_firmware())
        # clickable(self.mainWidget.qlabel_freqs).connect(lambda: self.read_freqs_file())
        self.mainWidget.qbutton_adu_fw.clicked.connect(lambda: self.download_firmware())
        self.mainWidget.qbutton_browse.clicked.connect(lambda: self.board_search())
        self.mainWidget.qbutton_connection.clicked.connect(lambda: self.board_connect())
        self.mainWidget.qbutton_adu_setup.clicked.connect(lambda: self.board_setup())
        # self.mainWidget.qbutton_adu_rate.clicked.connect(lambda: self.board_rate())
        self.mainWidget.qcombo_set_pll.currentIndexChanged.connect(self.select_sample_rate)
        # self.mainWidget.qcombo_supply.currentIndexChanged.connect(self.select_power_supply)
        self.mainWidget.qcombo_set_input.currentIndexChanged.connect(self.select_adu_input)
        # self.mainWidget.qbutton_psupply_enable.clicked.connect(lambda: self.enable_powersupply())
        self.mainWidget.qbutton_jig_enable.clicked.connect(lambda: self.jigConnect())
        clickable(self.mainWidget.qtext_preadu).connect(lambda: self.open_preadu_conf())
        # self.mainWidget.qbutton_selftest_start.clicked.connect(lambda: self.selfTest())
        # Signal Generator
        self.mainWidget.qbutton_gen_setup.clicked.connect(lambda: self.genSetup())

        # RF JIG
        self.mainWidget.qcombo_jig_rf.currentIndexChanged.connect(lambda: self.jig_set_rf_source())
        self.mainWidget.qcombo_jig_att.currentIndexChanged.connect(lambda: self.jig_set_attenuation())
        self.mainWidget.qcombo_jig_channel.currentIndexChanged.connect(lambda: self.jig_set_channel())
        self.mainWidget.qcombo_jig_filter.currentIndexChanged.connect(lambda: self.jig_set_filter())
        self.mainWidget.qbutton_acq_start.clicked.connect(lambda: self.snap())

        # Plots
        clickable(self.mainWidget.qtext_clear).connect(lambda: self.plotClear())
        clickable(self.mainWidget.qtext_save).connect(lambda: self.saveSingleSpectra())
        self.mainWidget.qbutton_ant_enable.clicked.connect(lambda: self.ant_enable())
        # self.mainWidget.qbutton_ant_save.clicked.connect(lambda: self.ant_save())
        # self.mainWidget.qbutton_ant_eq.clicked.connect(lambda: self.ant_eq())
        self.mainWidget.qcombo_ant_view.currentIndexChanged.connect(self.select_ant_view)
        self.mainWidget.qcombo_ant_select.currentIndexChanged.connect(self.reshapePlot)

    def board_search(self):
        self.itpm_ips = ip_scan()
        # print self.itpm_ips
        while self.mainWidget.qcombo_adu_ip.count() > 0:
            self.mainWidget.qcombo_adu_ip.removeItem(0)
        for f in self.itpm_ips:
            self.mainWidget.qcombo_adu_ip.addItem(f)

    def open_preadu_conf(self):
        if self.connected:
            self.preadu_dict = {
                'ipaddr': self.board_ip,
                'preadu_l': 'n/a',
                'preadu_r': 'n/a',
                'subrack_position': 'n/a',
                'serial': 'n/a'
            }
            self.preadu = tpm_preadu.preaduWindow(self.tpm, self.preadu_dict)
            self.preadu.show()

    def saveSingleSpectra(self):
        fname = datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()), "%Y%m%d_%H%M%S.txt")
        tname = easygui.filesavebox(msg=None, title="Saving Spectra data to text file",
                                    default="~/Documents/TPM-Data/" + fname, filetypes=["*.txt"])
        # print len(self.averaged_spectra),len(self.averaged_freqs)
        f = open(tname, "w")
        for i in xrange(len(self.averaged_spectra)):
            f.write(str(self.averaged_freqs[i]) + "\t" + str(self.averaged_spectra[i]) + "\n")
        f.close()
        print "Written text file: ", tname

    def select_ant_view(self):
        if self.mainWidget.qcombo_ant_view.currentIndex() < 3:
            self.reshapePlot()
            self.mainWidget.qframe_ant_rms.hide()
        elif self.mainWidget.qcombo_ant_view.currentIndex() == 3:
            self.mainWidget.plotWidgetAntFour.hide()
            self.mainWidget.plotWidgetAntOne.hide()
            self.mainWidget.plotWidgetAnt.hide()
            self.mainWidget.plotWidgetChart.hide()
            self.mainWidget.plotWidgetBar.show()

        elif self.mainWidget.qcombo_ant_view.currentIndex() == 4:
            self.mainWidget.plotWidgetAntFour.hide()
            self.mainWidget.plotWidgetAntOne.hide()
            self.mainWidget.plotWidgetAnt.hide()
            self.mainWidget.plotWidgetChart.show()
            self.mainWidget.plotWidgetBar.hide()

        else:
            self.mainWidget.plotWidgetAnt.hide()
            self.mainWidget.plotWidgetAntFour.hide()
            self.mainWidget.plotWidgetAntOne.hide()
            self.mainWidget.plotWidgetChart.hide()
            self.mainWidget.plotWidgetBar.hide()
            self.mainWidget.qframe_ant_rms.show()
        self.updateAntennaTest()

    def reshapePlot(self):
        if self.mainWidget.qcombo_ant_view.currentIndex() < 3:
            if self.mainWidget.qcombo_ant_select.currentIndex() == 0:
                self.mainWidget.plotWidgetAntFour.hide()
                self.mainWidget.plotWidgetAntOne.hide()
                self.mainWidget.plotWidgetAnt.show()
                self.mainWidget.plotWidgetBar.hide()
                self.mainWidget.plotWidgetChart.hide()
            elif self.mainWidget.qcombo_ant_select.currentIndex() >= 1 and self.mainWidget.qcombo_ant_select.currentIndex() <= 4:
                self.mainWidget.plotWidgetAntFour.show()
                self.mainWidget.plotWidgetAntOne.hide()
                self.mainWidget.plotWidgetAnt.hide()
                self.mainWidget.plotWidgetBar.hide()
                self.mainWidget.plotWidgetChart.hide()
            else:
                self.mainWidget.plotWidgetAntFour.hide()
                self.mainWidget.plotWidgetAntOne.show()
                self.mainWidget.plotWidgetAnt.hide()
                self.mainWidget.plotWidgetBar.hide()
                self.mainWidget.plotWidgetChart.hide()

    def create_ant_table(self):
        self.ant_rms_adurms = []
        self.ant_rms_title = []
        for i in xrange(32):
            self.ant_rms_adurms += [
                create_label(self.mainWidget.qframe_ant_rms, ((i % 8) * 130 + ((((i + 1) % 8) % 2) * 30)),
                             50 + ((i / 8) * 140), "-")]
        for i in xrange(16):
            self.ant_rms_title += [
                create_label(self.mainWidget.qframe_ant_rms, 80 + ((i % 4) * 260), 10 + ((i / 4) * 140),
                             "ANT " + str(i + 1))]

    def ant_enable(self):
        # if self.connected==True and fpgaIsProgrammed(self.tpm, 0):
        if not self.ant_test_enabled:
            self.ant_test_Thread = True
            self.ant_test_enabled = True
            self.mainWidget.qbutton_ant_enable.setText("DISABLE")
            print "\nStart Antenna Measurements\n"
            if not self.process_antenna_test.isAlive():
                self.process_antenna_test.start()
        else:
            self.ant_test_Thread = False
            self.ant_test_enabled = False
            self.mainWidget.qbutton_ant_enable.setText("ENABLE")
            print "\nStop Antenna Measurements\n"

    def ant_save(self):
        self.mainWidget.plotWidgetAnt.hide()

    def ant_eq(self):
        self.mainWidget.plotWidgetAnt.show()

    def ant_test_single(self):
        map_tpm = [1, 0, 3, 2, 5, 4, 7, 6, 17, 16, 19, 18, 21, 20, 23, 22, 30, 31, 28, 29, 26, 27, 24, 25, 14, 15, 12,
                   13, 10, 11, 8, 9]
        map_adu = range(32)
        if self.mainWidget.qcombo_ant_names.currentIndex() == 0:
            remap = map_adu
        else:
            remap = map_tpm
        # print "RUN", len(self.snapTPM()[0]), len(self.snapTPM()[0][0])
        dati = self.snapTPM()[0]
        # print "DATA", len(dati), dati[0][0:5]
        spettro = []
        # n=8192*4 # split and average number, from 128k to 16 of 8k  federico qui ne medi 8
        n = 1024  # split and average number, from 128k to 16 of 8k qui ne medi 128
        # freqs=self.calcFreqs(len(dati[0])/16*4) #modified federico
        freqs = self.calcFreqs(len(dati[0]) / 128)
        # print "Freqs ",len(freqs)
        for i in xrange(32):
            l = dati[remap[i]]
            sp = [l[remap[i]:remap[i] + n] for remap[i] in xrange(0, len(l), n)]
            # print "SPLITTED",len(sp), len(sp[0])
            singoli = np.zeros(len(self.plot_spectra(sp[0])))
            # print "CHUNK" ,len(singoli)
            for k in sp:
                # print "K", len(k)
                singolo = self.plot_spectra(k)
                # print "Spettro", len(singolo), singolo[0:5]
                singoli[:] += singolo
                # print "Loop"
            singoli[:] /= 128  # 16
            spettro += [singoli]
        # print "spettro", len(spettro), spettro[0][0:5]
        # print "End of ant_test_single"

        # fixme
        return freqs, spettro, np.array(dati, dtype=np.float64)

    def closeEvent(self, event):
        result = QtGui.QMessageBox.question(self,
                                            "Confirm Exit...",
                                            "Are you sure you want to exit ?",
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        event.ignore()

        if result == QtGui.QMessageBox.Yes:
            event.accept()
            self.haltThread = True
            self.connected = False
            self.stopThreads = True
            print "Stopping Threads"
            time.sleep(1)

    def snap(self):
        if self.ready:
            if self.mainWidget.qcombo_acq_type.currentIndex() == 0:
                # FFT Single
                self.plotFFTSingle()
            elif self.mainWidget.qcombo_acq_type.currentIndex() == 1:
                # FFT Average
                self.plotFFTAvg()
            elif self.mainWidget.qcombo_acq_type.currentIndex() == 2:
                # FFT Average
                self.plotTimeDomain()
        else:
            print "ADU must be switched on, connected and configured before to snap data!"

    def plot_spectra(self, vett):
        # spettro=np.zeros(len(vett)/2) # rem 1
        # print "Doing spectrum of ", len(vett), "samples"
        window = np.hanning(len(vett))
        # print "Windowing"
        spettro = np.fft.rfft(vett * window)  # vedere se spettro[:]= accelera
        # print "Computed Spectrum"
        N = len(spettro)
        acf = 2  # amplitude correction factor
        spettro[:] = abs((acf * spettro) / N)
        with np.errstate(divide='ignore', invalid='ignore'):
            spettro[:] = 20 * np.log10(spettro / 127.0)
        # dB_FS = 10*log10(sum(abs(time_data(:,(n_time_record*(m-1))+1)).^2)/size(time_data(:,(n_time_record*(m-1))+1),1))-10*log10(0.5);
        # print "End of subroutine"
        return (np.real(spettro))

    def calcFreqs(self, lenvett):
        x = np.arange(0, lenvett, 1)
        freqs = np.fft.rfftfreq(x.shape[-1])
        freqs[:] = freqs * self.sample_rate  # modificato
        return freqs

    def snapTPM(self):
        try:
            UDP_PORT = 0x1234 + int(self.board_ip.split(".")[-1])
            done = 0
            sdp = sdp_med(UDP_PORT)
            misure = []
            # while(done != num or num == 0):
            snap = sdp.reassemble()
            channel_id_list = snap[4:4 + int(snap[3])]
            channel_list = snap[4 + int(snap[3]):]

            # done += 1
            # sys.stdout.write("\rAcq # %d/%d " %(done,num))
            # sys.stdout.flush()
            m = 0
            dati = []
            for n in range(len(channel_id_list)):
                if channel_id_list[n] == "1":
                    # last_filename=save_raw(path, channel_list[m],n,done)
                    dati += [channel_list[m]]
                    # print len(data)
                    m += 1
            misure += [dati]
            del sdp
            del dati
            del channel_list
            # ?print
            return misure
        except:
            print "Unable to snap data!"
            pass

    def updateProgressBar(self, val, text=""):
        self.mainWidget.qprogressBarACQ.setValue(int(val))
        self.mainWidget.qlabel_progress.setText(text)

    def plotFFTSingle(self, progress=True):
        data = self.snapTPM()[0][self.mainWidget.qcombo_adu_channel.currentIndex()]
        freqs = self.calcFreqs(len(data))
        spettro = self.plot_spectra(data)
        self.matlabPlotACQ.plotCurve(freqs, spettro, yAxisRange=[-100, 0],
                                     title=self.mainWidget.qcombo_adu_channel.currentText(), xLabel="MHz",
                                     yLabel="dBFS", plotLog=True)
        if progress:
            self.updateProgressBar(100)

    def plotFFTAvg(self, progress=True):
        adu_input = int(self.mainWidget.qcombo_adu_channel.currentIndex())
        avg_num = int(self.mainWidget.qtext_acq_avgnum.text())
        for i in xrange(avg_num):
            data = self.snapTPM()[0][adu_input]
            if progress:
                self.updateProgressBar(i * 100. / avg_num, "Downloading...")
            freqs = self.calcFreqs(len(data))
            spettro = self.plot_spectra(data)
            if i == 0:
                spettri = np.zeros(len(spettro))
            spettro = np.array(spettro)
            spettri = spettri + spettro
        self.averaged_spectra = spettri / avg_num
        self.averaged_freqs = freqs
        self.matlabPlotACQ.plotCurve(self.averaged_freqs, self.averaged_spectra, yAxisRange=[-100, 0],
                                     title=self.mainWidget.qcombo_adu_channel.currentText(), xLabel="MHz",
                                     yLabel="dBFS", plotLog=True)
        self.updateProgressBar(100)

    def plotTimeDomain(self, progress=True):
        adu_input = int(self.mainWidget.qcombo_adu_channel.currentIndex())
        data = self.snapTPM()[0][self.mainWidget.qcombo_adu_channel.currentIndex()]
        if progress:
            self.updateProgressBar(50, "Plotting...")
        self.plotClear()
        self.matlabPlotACQ.plotCurve(xrange(len(data)), data, yAxisRange=[-150, 150],
                                     title=self.mainWidget.qcombo_adu_channel.currentText(), xLabel="samples",
                                     yLabel="ADU", plotLog=False)
        if progress:
            self.updateProgressBar(100)

    def plotClear(self):
        self.matlabPlotACQ.plotClear()

    # def select_power_supply(self):
    #     if self.mainWidget.qcombo_supply.currentIndex()==1:
    #         try:
    #             self.supply = VISAHP6033A()
    #             #self.supply.disable()
    #             self.supply.set_volt(self.mainWidget.qtext_power_volt.text())
    #             self.supply.set_amp(self.mainWidget.qtext_power_amps.text())
    #             #self.process_read_amps = Thread(target=self.read_adu_amps)
    #             #self.process_read_amps.start()
    #             time.sleep(0.3)
    #             if self.amps>0.5:
    #                 self.mainWidget.qbutton_psupply_enable.setText("SWITCH OFF")
    #                 self.powered = True
    #             else:
    #                 self.mainWidget.qbutton_psupply_enable.setText("SWITCH ON")
    #                 self.powered = False
    #         except:
    #             self.mainWidget.qcombo_supply.setCurrentIndex(0)
    #             #print "Unable to connect with VISA GPIB (addr:4) HP6033A Power Supply!"
    #             pass
    #     else:
    #         print "Message: Using external PSU"
    #
    #
    # def enable_powersupply(self):
    #     if self.mainWidget.qcombo_supply.currentIndex()==1:
    #         if not self.powered:
    #             try:
    #                 self.supply.enable()
    #                 self.powered = True
    #                 #self.mainWidget.qbutton_psupply_enable.setText("SWITCH OFF")
    #                 #time.sleep(1)
    #             except:
    #                 print "Unable to connect with VISA GPIB (addr:4) HP6033A Power Supply!"
    #         else:
    #             try:
    #                 self.supply.disable()
    #                 self.powered = False
    #                 #self.mainWidget.qbutton_psupply_enable.setText("SWITCH ON")
    #                 self.board_connect(False)
    #
    #             except:
    #                 print "QT: Unable to connect with VISA GPIB (addr:4) HP6033A Power Supply!"

    def genSetup(self):
        if self.mainWidget.qcombo_gen_link.currentIndex() == 0:
            if self.mainWidget.qcombo_gen_type.currentIndex() == 0:
                try:
                    from SMY02 import RS_SMY02
                    self.gen = RS_SMY02()
                    try:
                        freq = float(self.mainWidget.qtext_gen_set_freq.text()) * (
                                    10 ** (self.mainWidget.qcombo_gen_unit.currentIndex() * 3))
                        # print freq, "Hz"
                        self.gen.set_rf(freq)
                        self.gen.set_level(float(self.mainWidget.qtext_gen_set_level.text()))
                    except:
                        print "Bad arguments format commanding the signal generator"
                        pass
                    del self.gen
                except:
                    print "Signal Generator Connection Failure (" + self.mainWidget.qcombo_gen_type.currentText() + " - " + self.mainWidget.qcombo_gen_link.currentText() + ")"
            else:
                try:
                    from SMX import RS_SMX
                    self.gen = RS_SMX()
                    try:
                        freq = float(self.mainWidget.qtext_gen_set_freq.text()) * (
                                    10 ** (self.mainWidget.qcombo_gen_unit.currentIndex() * 3))
                        # print freq, "Hz"
                        self.gen.set_rf(freq)
                        self.gen.set_level(float(self.mainWidget.qtext_gen_set_level.text()))
                    except:
                        print "Bad arguments format commanding the signal generator"
                        pass
                    del self.gen
                except:
                    print "Signal Generator Connection Failure (" + self.mainWidget.qcombo_gen_type.currentText() + " - " + self.mainWidget.qcombo_gen_link.currentText() + ")"

    def jigConnect(self):
        # JIG: Configuring Power Sensor    
        try:
            self.jig = RF_Jig(ip="", boardip=self.mainWidget.qtext_jig_ip.text(), port=10000, timeout=1)
            self.jig.Connect()
            self.mainWidget.qtext_jig_connected.setStyleSheet(colors('black_on_green'))
            self.mainWidget.qtext_jig_connected.setText("ONLINE")
            self.jig_set_rf_source()
            self.jig_set_attenuation()  # (63) Att=0
            self.jig_filter = NAME_FILTER[self.mainWidget.qcombo_jig_filter.currentIndex()][1]  # 50-80 MHz
            self.jig_set_filter()
            self.jig_set_channel()  # set channel 0 on switch path
            self.mainWidget.qbutton_jig_enable.setText("ENABLED")
            self.process_read_jigpm = Thread(target=self.read_jig_pm)
            self.process_read_jigpm.start()

        except:
            self.mainWidget.qtext_jig_connected.setStyleSheet(colors('white_on_red'))
            self.mainWidget.qtext_jig_connected.setText("OFFLINE")
            print "ERROR: Unable to connect with JIG (IP: " + self.mainWidget.qtext_jig_ip.text() + ")"

    def jig_set_rf_source(self):
        if not self.jig == None:
            try:
                if self.mainWidget.qcombo_jig_rf.currentIndex() == 0:
                    self.jig.set_input_mode(Inputmode.ext_gen)
                else:
                    self.jig.set_input_mode(Inputmode.ext_gen)
            except:
                print "ERROR: Unable to connect with JIG (IP: " + self.mainWidget.qtext_jig_ip.text() + ")"
        else:
            print "ERROR: Connect to a JIG device before to setup!"

    def jig_set_attenuation(self):
        if not self.jig == None:
            try:
                self.jig.set_gain(63 - int(self.mainWidget.qcombo_jig_att.currentIndex()))
            except:
                print "ERROR: Unable to connect with JIG (IP: " + self.mainWidget.qtext_jig_ip.text() + ")"
        else:
            print "ERROR: Connect to a JIG device before to setup!"

    def jig_set_channel(self):
        if not self.jig == None:
            try:
                if self.mainWidget.qcombo_jig_channel.currentIndex() < 32:
                    self.jig.set_outmode(self.mainWidget.qcombo_jig_channel.currentIndex())
                else:
                    self.jig.set_outmode(255)
            except:
                print "ERROR: Unable to connect with JIG (IP: " + self.mainWidget.qtext_jig_ip.text() + ")"
        else:
            print "ERROR: Connect to a JIG device before to setup!"

    def jig_set_filter(self):
        if not self.jig == None:
            try:
                self.jig_filter = NAME_FILTER[self.mainWidget.qcombo_jig_filter.currentIndex()][1]  # 50-80 MHz
                self.jig.set_filter(self.jig_filter)
            except:
                print "ERROR: Unable to connect with JIG (IP: " + self.mainWidget.qtext_jig_ip.text() + ")"
        else:
            print "ERROR: Connect to a JIG device before to setup!"

    def updateUI(self):
        time.sleep(0.5)
        if self.connected:
            # if cmd_ping(self.tpm_config[0]['ipaddr']) == 0:
            self.connected = True
            self.mainWidget.qtext_connected.setStyleSheet(colors("black_on_green"))
            self.mainWidget.qtext_connected.setText("ONLINE")
            # self.mainWidget.qtext_preadu
            self.mainWidget.qlabel_cpld_fw.setText("CPLD: " + getCpldFwVersion(self.tpm))
            self.mainWidget.qlabel_cpld_fw.setStyleSheet(colors("black_on_green"))
            if fpgaIsProgrammed(self.tpm, 0):
                self.mainWidget.qtext_fpga0.setStyleSheet(colors('black_on_green'))
                self.mainWidget.qlabel_fpga_fw.setText("FPGA: " + getFpgaFwVersion(self.tpm))
                self.mainWidget.qlabel_fpga_fw.setStyleSheet(colors("black_on_green"))
            else:
                self.mainWidget.qtext_fpga0.setStyleSheet(colors('white_on_red'))
                self.mainWidget.qlabel_fpga_fw.setText("FPGA FW Version")
                self.mainWidget.qlabel_fpga_fw.setStyleSheet(colors("white_on_red"))
            if fpgaIsProgrammed(self.tpm, 1):
                self.mainWidget.qtext_fpga1.setStyleSheet(colors('black_on_green'))
            else:
                self.mainWidget.qtext_fpga1.setStyleSheet(colors('white_on_red'))
            if isPreaduOn(self.tpm):
                self.mainWidget.qtext_preadu.setStyleSheet(colors('black_on_green'))
            else:
                self.mainWidget.qtext_preadu.setStyleSheet(colors('white_on_red'))
            if getPLLStatus(self.tpm) == 0xe7:
                self.mainWidget.qtext_adu_pll_lock.setStyleSheet(colors('black_on_green'))
                self.mainWidget.qtext_adu_pll_lock.setText("LOCKED")
                self.mainWidget.qtext_adu_pll_ref.setStyleSheet(colors('black_on_green'))
                self.mainWidget.qtext_adu_pll_ref.setText("EXTERNAL")
            elif getPLLStatus(self.tpm) == 0xf2:
                self.mainWidget.qtext_adu_pll_lock.setStyleSheet(colors('black_on_green'))
                self.mainWidget.qtext_adu_pll_lock.setText("LOCKED")
                self.mainWidget.qtext_adu_pll_ref.setStyleSheet(colors('black_on_green'))
                self.mainWidget.qtext_adu_pll_ref.setText("INTERNAL")
            else:
                self.mainWidget.qtext_adu_pll_lock.setStyleSheet(colors('white_on_red'))
                self.mainWidget.qtext_adu_pll_lock.setText("UNLOCKED")
                self.mainWidget.qtext_adu_pll_ref.setStyleSheet(colors('white_on_red'))
                self.mainWidget.qtext_adu_pll_ref.setText("REF INT/EXT")
            if getADCStatus(self.tpm) == 0:
                self.mainWidget.qtext_adc.setStyleSheet(colors('white_on_red'))
            else:
                self.mainWidget.qtext_adc.setStyleSheet(colors('black_on_green'))
                self.ready = True
            # PPS Test
            if ((not self.tpm.rmp.rd32(0 * 0x10000000 + 0x90020) == 0) and
                    (not self.tpm.rmp.rd32(1 * 0x10000000 + 0x90020) == 0)):
                self.mainWidget.qtext_pps.setStyleSheet(colors('black_on_green'))
            else:
                self.mainWidget.qtext_pps.setStyleSheet(colors('white_on_red'))

        else:
            self.connected = False
            self.mainWidget.qtext_connected.setStyleSheet(colors("white_on_red"))
            self.mainWidget.qtext_connected.setText("OFFLINE")
            self.mainWidget.qtext_preadu.setStyleSheet(colors('white_on_red'))
            self.mainWidget.qtext_fpga0.setStyleSheet(colors('white_on_red'))
            self.mainWidget.qtext_fpga1.setStyleSheet(colors('white_on_red'))
            self.mainWidget.qlabel_fpga_fw.setText("FPGA FW Version")
            self.mainWidget.qlabel_fpga_fw.setStyleSheet(colors("white_on_red"))
            self.mainWidget.qlabel_cpld_fw.setText("CPLD FW Version")
            self.mainWidget.qlabel_cpld_fw.setStyleSheet(colors("white_on_red"))
            self.mainWidget.qtext_adu_pll_lock.setStyleSheet(colors('white_on_red'))
            self.mainWidget.qtext_adu_pll_lock.setText("UNLOCKED")
            self.mainWidget.qtext_adu_pll_ref.setStyleSheet(colors('white_on_red'))
            self.mainWidget.qtext_adu_pll_ref.setText("REF INT/EXT")
            self.mainWidget.qtext_adc.setStyleSheet(colors('white_on_red'))
            self.mainWidget.qtext_pps.setStyleSheet(colors('white_on_red'))

            # self.mainWidget.qtext_meas_temp.setText("n/a")
            # self.mainWidget.qtext_meas_temp.setStyleSheet(colors("white_on_red"))
            # self.mainWidget.qtext_adu_temp.setText("Temp: ---")
            # self.mainWidget.qtext_adu_temp.setStyleSheet(colors("white_on_red"))
            self.goThread = False

    def read_hk(self):
        while (True):

            # Temperature of ADU via ADU REGISTERS 
            if self.connected:
                if not self.haltThreadTemp:
                    try:
                        self.temperatura = getTpmTemp(self.tpm)
                        # print self.temperatura," deg."
                    except:
                        self.temperatura = -100
                        print "********************************"
                        pass

            # Current Absortion via Power Supply Comm
            if not self.haltThread and self.powered:
                try:
                    self.amps = self.supply.read_amps()
                except:
                    self.amps = -10
                    pass
                time.sleep(0.2)
            self.housekeeping_signal.emit()

            cycle = 0.0
            while cycle < 5:
                time.sleep(0.5)
                cycle = cycle + 0.5
            if self.stopThreads:
                break

    def updateHK(self):
        if self.connected and not self.haltThreadTemp:
            self.updateTemp()

    def read_jig_pm(self):
        while True:
            cycle = 0.0
            # while not self.haltThreadTemp and cycle<5:
            while cycle < 5:
                time.sleep(0.5)
                cycle = cycle + 0.5
            if self.mainWidget.qtext_jig_connected.text() == "ONLINE":
                self.jig_pm_signal.emit()
            if self.stopThreads:
                break

    def snap_antenna(self):
        while True:
            # if self.connected==True and fpgaIsProgrammed(self.tpm, 0):
            if self.ant_test_enabled:
                try:
                    # prendi dati
                    # print "Snap data, then emit signal"
                    self.adu_rms = np.zeros(32)
                    if not self.stopThreads and self.ant_test_enabled:
                        # print "Snapping..."
                        self.freqs, self.spettro_mediato, self.dati = self.ant_test_single()  # riordinare in funzione della mappa  adu_rs etcetc
                        if self.ant_test_enabled:
                            sys.stdout.write("\rAcquisition: #%d ...downloading...                 " % (
                                        self.antenna_test_acq_num + 1))
                            sys.stdout.flush()
                        self.adu_rms = self.adu_rms + np.sqrt(np.mean(np.power(self.dati, 2), 1))
                    self.adu_rms_buffer += self.adu_rms.tolist()
                    self.volt_rms = self.adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
                    with np.errstate(divide='ignore', invalid='ignore'):
                        self.power_adc = 10 * np.log10(np.power(self.volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
                    self.power_rf = self.power_adc + 12  # single ended to diff net loose 12 dBm
                    # print self.adu_rms[0], self.volt_rms[0], self.power_adc[0], self.power_rf[0]
                    # print "Mediati!"
                    self.antenna_test_acq_num = self.antenna_test_acq_num + 1
                    # print "Emitting Signal"
                    if self.ant_test_enabled:
                        sys.stdout.write(
                            "\rAcquisition: #%d ...refreshing plots/tables..." % (self.antenna_test_acq_num))
                        sys.stdout.flush()
                    self.antenna_test_signal.emit()

                except:
                    print "Unable to snap data during Antenna Test"
                    pass
            cycle = 0.0
            while cycle < 1 and not self.stopThreads and self.ant_test_enabled:
                time.sleep(0.5)
                cycle = cycle + 0.5
            if self.stopThreads:
                break

    def updateAntennaTest(self):
        map_tpm = [1, 0, 3, 2, 5, 4, 7, 6, 17, 16, 19, 18, 21, 20, 23, 22, 30, 31, 28, 29, 26, 27, 24, 25, 14, 15, 12,
                   13, 10, 11, 8, 9]
        map_adu = range(32)
        if self.mainWidget.qcombo_ant_names.currentIndex() == 0:
            remap = map_adu
        else:
            remap = map_tpm

        if self.ant_test_enabled:
            # print "Signal emitted"
            self.xAxisRange = [float(self.mainWidget.qtext_xmin.text()), float(self.mainWidget.qtext_xmax.text())]
            self.yAxisRange = [float(self.mainWidget.qtext_ymin.text()), float(self.mainWidget.qtext_ymax.text())]
            if self.mainWidget.qcombo_ant_view.currentIndex() == 0:  # Plots  Dual Pol
                # print "Checking"
                if self.mainWidget.qcombo_ant_select.currentIndex() == 0:  # 16 Plots
                    # print "Starting plot 16 antennas"
                    self.miniPlots.plotClear()
                    for i in xrange(32):
                        if i % 32 % 2 == 0:  # solo pari
                            plotcolor = "b"
                        else:
                            plotcolor = "g"
                        # print i,len(self.freqs),len(self.spettro_mediato[i])
                        self.miniPlots.plotCurve(self.freqs, self.spettro_mediato[i], i / 2, xAxisRange=self.xAxisRange,
                                                 yAxisRange=self.yAxisRange, title="ANT " + str(i / 2 + 1),
                                                 xLabel="MHz", yLabel="dBFS", plotLog=True, colore=plotcolor)
                    self.miniPlots.updatePlot()

                elif self.mainWidget.qcombo_ant_select.currentIndex() >= 1 and self.mainWidget.qcombo_ant_select.currentIndex() <= 4:  # 4 Plots
                    self.miniPlotsFour.plotClear()
                    for i in self.groupAntennaPlot[self.mainWidget.qcombo_ant_select.currentIndex() - 1]:
                        if i % 32 % 2 == 0:  # solo pari
                            plotcolor = "b"
                        else:
                            plotcolor = "g"
                        self.miniPlotsFour.plotCurve(self.freqs, self.spettro_mediato[i], i % 8 / 2,
                                                     xAxisRange=self.xAxisRange, yAxisRange=self.yAxisRange,
                                                     title="ANT " + str(i / 2 + 1), xLabel="MHz", yLabel="dBFS",
                                                     plotLog=True, colore=plotcolor)
                    self.miniPlotsFour.updatePlot()

                else:  # 1 Plot
                    self.miniPlotsOne.plotClear()
                    self.miniPlotsOne.plotCurve(self.freqs, self.spettro_mediato[
                        (self.mainWidget.qcombo_ant_select.currentIndex() - 5) * 2], 0, xAxisRange=self.xAxisRange,
                                                yAxisRange=self.yAxisRange, title="ANT " + str(
                            self.mainWidget.qcombo_ant_select.currentIndex() - 5 + 1), xLabel="MHz", yLabel="dBFS",
                                                plotLog=True, colore="b")
                    self.miniPlotsOne.plotCurve(self.freqs, self.spettro_mediato[
                        (self.mainWidget.qcombo_ant_select.currentIndex() - 5) * 2 + 1], 0, xAxisRange=self.xAxisRange,
                                                yAxisRange=self.yAxisRange, title="ANT " + str(
                            self.mainWidget.qcombo_ant_select.currentIndex() - 5 + 1), xLabel="MHz", yLabel="dBFS",
                                                plotLog=True, colore="g")
                    self.miniPlotsOne.updatePlot()

            if self.mainWidget.qcombo_ant_view.currentIndex() == 1:  # Plots  X
                plotcolor = "b"
                # print "Checking"
                if self.mainWidget.qcombo_ant_select.currentIndex() == 0:  # 16 Plots
                    # print "Starting plot 16 antennas"
                    self.miniPlots.plotClear()
                    for i in xrange(32):
                        # print i,len(self.freqs),len(self.spettro_mediato[i])
                        if i % 32 % 2 == 0:  # solo pari
                            self.miniPlots.plotCurve(self.freqs, self.spettro_mediato[i], i / 2,
                                                     xAxisRange=self.xAxisRange, yAxisRange=self.yAxisRange,
                                                     title="ANT " + str(i + 1), xLabel="MHz", yLabel="dBFS",
                                                     plotLog=True, colore=plotcolor)
                    self.miniPlots.updatePlot()

                elif self.mainWidget.qcombo_ant_select.currentIndex() >= 1 and self.mainWidget.qcombo_ant_select.currentIndex() <= 4:  # 4 Plots
                    self.miniPlotsFour.plotClear()
                    for i in self.groupAntennaPlot[self.mainWidget.qcombo_ant_select.currentIndex() - 1]:
                        if i % 32 % 2 == 0:  # solo pari
                            self.miniPlotsFour.plotCurve(self.freqs, self.spettro_mediato[i], i % 8 / 2,
                                                         xAxisRange=self.xAxisRange, yAxisRange=self.yAxisRange,
                                                         title="ANT " + str(i / 2 + 1), xLabel="MHz", yLabel="dBFS",
                                                         plotLog=True, colore=plotcolor)
                    self.miniPlotsFour.updatePlot()

                else:  # 1 Plot
                    self.miniPlotsOne.plotClear()
                    self.miniPlotsOne.plotCurve(self.freqs, self.spettro_mediato[
                        (self.mainWidget.qcombo_ant_select.currentIndex() - 5) * 2], 0, xAxisRange=self.xAxisRange,
                                                yAxisRange=self.yAxisRange, title="ANT " + str(
                            self.mainWidget.qcombo_ant_select.currentIndex() - 5 + 1), xLabel="MHz", yLabel="dBFS",
                                                plotLog=True, colore=plotcolor)
                    # self.miniPlotsOne.plotCurve(self.freqs, self.spettro_mediato[(self.mainWidget.qcombo_ant_select.currentIndex()-5)*2+1], 0, yAxisRange = self.yAxisRange, title="ANT "+str((self.mainWidget.qcombo_ant_select.currentIndex()-5)*2+1), xLabel="MHz", yLabel="dBFS", plotLog=True)
                    self.miniPlotsOne.updatePlot()

            if self.mainWidget.qcombo_ant_view.currentIndex() == 2:  # Plots  Y
                plotcolor = "g"
                # print "Checking"
                if self.mainWidget.qcombo_ant_select.currentIndex() == 0:  # 16 Plots
                    # print "Starting plot 16 antennas"
                    self.miniPlots.plotClear()
                    for i in xrange(32):
                        # print i,len(self.freqs),len(self.spettro_mediato[i])
                        if i % 32 % 2 == 1:  # solo dispari
                            self.miniPlots.plotCurve(self.freqs, self.spettro_mediato[i], i / 2,
                                                     xAxisRange=self.xAxisRange, yAxisRange=self.yAxisRange,
                                                     title="ANT " + str(i + 1), xLabel="MHz", yLabel="dBFS",
                                                     plotLog=True, colore=plotcolor)
                    self.miniPlots.updatePlot()

                elif self.mainWidget.qcombo_ant_select.currentIndex() >= 1 and self.mainWidget.qcombo_ant_select.currentIndex() <= 4:  # 4 Plots
                    self.miniPlotsFour.plotClear()
                    for i in self.groupAntennaPlot[self.mainWidget.qcombo_ant_select.currentIndex() - 1]:
                        if i % 32 % 2 == 1:  # solo dispari
                            self.miniPlotsFour.plotCurve(self.freqs, self.spettro_mediato[i], i % 8 / 2,
                                                         xAxisRange=self.xAxisRange, yAxisRange=self.yAxisRange,
                                                         title="ANT " + str(i / 2 + 1), xLabel="MHz", yLabel="dBFS",
                                                         plotLog=True, colore=plotcolor)
                    self.miniPlotsFour.updatePlot()

                else:  # 1 Plot
                    self.miniPlotsOne.plotClear()
                    # self.miniPlotsOne.plotCurve(self.freqs, self.spettro_mediato[(self.mainWidget.qcombo_ant_select.currentIndex()-5)*2], 0, yAxisRange = self.yAxisRange, title="ANT "+str((self.mainWidget.qcombo_ant_select.currentIndex()-5)*2), xLabel="MHz", yLabel="dBFS", plotLog=True)
                    self.miniPlotsOne.plotCurve(self.freqs, self.spettro_mediato[
                        (self.mainWidget.qcombo_ant_select.currentIndex() - 5) * 2 + 1], 0, xAxisRange=self.xAxisRange,
                                                yAxisRange=self.yAxisRange, title="ANT " + str(
                            self.mainWidget.qcombo_ant_select.currentIndex() - 5 + 1), xLabel="MHz", yLabel="dBFS",
                                                plotLog=True, colore=plotcolor)
                    self.miniPlotsOne.updatePlot()

            elif self.mainWidget.qcombo_ant_view.currentIndex() == 3:  # ADU RMS Bar Plot
                self.RMSbarPlot.plotBar(self.adu_rms)

            elif self.mainWidget.qcombo_ant_view.currentIndex() == 4:  # ADU RMS Chart
                self.RMSChartPlot.plotChart(self.adu_rms_buffer)

            elif self.mainWidget.qcombo_ant_view.currentIndex() == 5:  # ADU RMS Table
                for i in xrange(32):
                    self.ant_rms_adurms[i].setText("%3.1f" % (self.adu_rms[remap[i]]))

            elif self.mainWidget.qcombo_ant_view.currentIndex() == 6:  # Volt RMS Table
                for i in xrange(32):
                    self.ant_rms_adurms[i].setText("%3.1f" % (self.volt_rms[i]))

            elif self.mainWidget.qcombo_ant_view.currentIndex() == 7:  # ADC Power Table
                for i in xrange(32):
                    self.ant_rms_adurms[i].setText("%3.1f" % (self.power_adc[i]))

            else:  # RF Power Table
                for i in xrange(32):
                    self.ant_rms_adurms[i].setText("%3.1f" % (self.power_rf[remap[i]]))

            self.mainWidget.qlabel_ant_num.setText("Acquisition Number: " + str(self.antenna_test_acq_num))

    def updateJIGpm(self):
        if self.mainWidget.qtext_jig_connected.text() == "ONLINE":
            ch = int(self.mainWidget.qcombo_jig_channel.currentIndex() & 31)
            freq = float(self.mainWidget.qtext_gen_set_freq.text()) * (
                        10 ** (self.mainWidget.qcombo_gen_unit.currentIndex() * 3))
            self.mainWidget.qlabel_jig_power.setText("%3.1f dBm" % (self.jig.read_power(ch, freq)))

    def updateTemp(self):
        if self.connected:
            # print "ciao ",self.temperatura, (not self.temperatura=="---")
            if not self.temperatura == -100:
                self.mainWidget.qtext_adu_temp.setText("Temp: %3.1f" % (self.temperatura))
                # self.mainWidget.qtext_meas_temp.setText("%3.1f"%(self.temperatura))
                if self.temperatura > 60 and self.temperatura < 66:
                    self.mainWidget.qtext_adu_temp.setStyleSheet(colors("black_on_yellow"))
                    # self.mainWidget.qtext_meas_temp.setStyleSheet(colors("black_on_yellow"))
                elif self.temperatura >= 66:
                    self.mainWidget.qtext_adu_temp.setStyleSheet(colors("white_on_red"))
                    # self.mainWidget.qtext_meas_temp.setStyleSheet(colors("white_on_red"))
                else:
                    self.mainWidget.qtext_adu_temp.setStyleSheet(colors("black_on_green"))
                    # self.mainWidget.qtext_meas_temp.setStyleSheet(colors("black_on_green"))
            else:
                self.mainWidget.qtext_adu_temp.setStyleSheet(colors("white_on_red"))
                self.mainWidget.qtext_adu_temp.setText("Temp: ---")
                # self.mainWidget.qtext_meas_temp.setStyleSheet(colors("white_on_red"))
                # self.mainWidget.qtext_meas_temp.setText("n/a")
        else:
            # self.mainWidget.qtext_meas_temp.setText("n/a")
            # self.mainWidget.qtext_meas_temp.setStyleSheet(colors("white_on_red"))
            self.mainWidget.qtext_adu_temp.setText("Temp: ---")
            self.mainWidget.qtext_adu_temp.setStyleSheet(colors("white_on_red"))

    def select_sample_rate(self):
        if self.mainWidget.qcombo_set_pll.currentIndex() == 0:
            self.sample_rate = 800
        elif self.mainWidget.qcombo_set_pll.currentIndex() == 1:
            self.sample_rate = 700
        elif self.mainWidget.qcombo_set_pll.currentIndex() == 2:
            self.sample_rate = 1000
        else:
            # default 800
            self.sample_rate = 800

    def select_adu_input(self):
        if self.mainWidget.qcombo_set_input.currentIndex() == 0:
            self.adu_input = "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31"
        elif self.mainWidget.qcombo_set_input.currentIndex() == 1:
            self.adu_input = "0,8,16,24"
        else:
            # default 800
            self.adu_input = "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31"

    def board_connect(self, on=True):
        if on:
            if not self.connected:
                # self.tpm = TPM(ip=self.tpm_config[0]['ipaddr'], port=self.tpm_config[0]['udpport'], timeout=self.tpm_config[0]['udptimeout'])
                self.config = config_man.get_config_from_file(config_file="../config/config.txt", design="tpm_test",
                                                              display=False, check=False, sim="")
                self.tpm = TPM(ip=self.mainWidget.qcombo_adu_ip.currentText(), port=self.tpm_config[0]['udpport'],
                               timeout=self.tpm_config[0]['udptimeout'])
                self.tpm.load_firmware_blocking(Device.FPGA_1, self.config['XML_FILE'])
                try:
                    prova = self.tpm[0]
                    self.connected = True
                    self.board_ip = str(self.mainWidget.qcombo_adu_ip.currentText())
                    self.haltThreadTemp = False
                    print "\nSuccessfully connected with TPM IP ", self.mainWidget.qcombo_adu_ip.currentText()
                    self.mainWidget.qbutton_connection.setText("DISCONNECT")
                except:
                    print "\nUnable to connect to TPM board ( IP:", self.mainWidget.qcombo_adu_ip.currentText(), ")"
                    self.connected = False
                    del self.tpm
                    self.mainWidget.qbutton_connection.setText("CONNECT")
                    pass
            else:
                del self.tpm  # = None
                self.connected = False
                self.haltThreadTemp = True
                self.haltThread = True
                time.sleep(0.5)
                self.mainWidget.qtext_adu_temp.setText("Temp: ---")
                self.mainWidget.qtext_adu_temp.setStyleSheet(colors("white_on_red"))
                self.mainWidget.qbutton_connection.setText("CONNECT")
                print "\nDisconnected from TPM ", self.board_ip
                self.updateUI()
        else:
            self.ready = False
            self.connected = False
            if not self.tpm == None:
                del self.tpm
            self.haltThreadTemp = True
            self.mainWidget.qtext_adu_temp.setText("Temp: ---")
            self.mainWidget.qtext_adu_temp.setStyleSheet(colors("white_on_red"))
            time.sleep(0.5)
        self.updateUI()
        if self.connected and not self.process_housekeeping.isAlive():
            print "\nStarted reading HK..."
            self.process_housekeeping.start()

    def board_setup(self):
        if self.connected:
            self.haltThread = True
            self.haltThreadTemp = True
            time.sleep(0.5)
            cmd = "python ../board/test.py -s "
            # if not self.tpm_config[0]['ipaddr'] == "10.0.10.2":
            cmd += "--ip=" + str(self.board_ip)
            if not self.sample_rate == 800:
                cmd += " -f " + str(self.sample_rate)
            cmd += " -i " + self.adu_input
            if self.mainWidget.checkBox_ADA.isChecked():
                cmd += " --ada"
            os.system(cmd + " --server-ip=10.0.10.200 ")
            time.sleep(0.5)
            self.updateUI()
            time.sleep(0.5)
            self.haltThread = False
            self.haltThreadTemp = False
            self.ready = True
            self.plotClear()
        else:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Please CONNECT to a TPM first...")
            msgBox.setWindowTitle("Error!")
            msgBox.exec_()

    def board_rate(self):
        if self.connected:
            if self.board_fast_rate:
                if subprocess.call(['python', '../board/reg.py', '3000000c', '1000', '--ip=' + self.board_ip],
                                   stdout=DEVNULL) == 0:
                    self.mainWidget.qbutton_adu_rate.setText("SLOW RATE")
                    self.board_fast_rate = False
            else:
                if subprocess.call(['python', '../board/reg.py', '3000000c', '1', '--ip=' + self.board_ip],
                                   stdout=DEVNULL) == 0:
                    self.mainWidget.qbutton_adu_rate.setText("FAST RATE")
                    self.board_fast_rate = True
        else:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Please CONNECT to a TPM first...")
            msgBox.setWindowTitle("Error!")
            msgBox.exec_()

    def download_firmware(self):
        if self.connected:
            if not self.mainWidget.qtext_adu_fw.text() == "":
                self.haltThread = True
                self.haltThreadTemp = True
                time.sleep(0.5)
                print "Board " + self.board_ip + ": Programming FPGAs...\n"
                result = self.tpm.bsp.fpga_erase_and_program([0, 1], self.mainWidget.qtext_adu_fw.text())
                n = 0
                result = 255
                while n < 3 and not result == 0:
                    if result == 0:
                        print "Board " + self.board_ip + ": FPGAs programmed!"
                    n = n + 1
                self.updateUI()
                time.sleep(0.5)
                self.haltThread = False
                self.haltThreadTemp = False
            else:
                msgBox = QtGui.QMessageBox()
                msgBox.setText("Please Select a valid iTPM Firmware bitstream file first...")
                msgBox.setWindowTitle("Error!")
                msgBox.exec_()
        else:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Please CONNECT to a TPM first...")
            msgBox.setWindowTitle("Error!")
            msgBox.exec_()

    def read_freqs_file(self):
        freqfile = easygui.fileopenbox(msg='Please select the frequencies file', default="Freqs\\")
        if not freqfile == "" or not freqfile == None:
            try:
                print("Opening file: %s" % (freqfile))
                # self.mainWidget.qtext_freqs.setText(freqfile)
                freq_file = open(freqfile, 'r')
                freqs = freq_file.readlines()
                # print "Found "+str(len(freqs))+" frequencies!\n"
                freq_file.close()
                while self.mainWidget.qcombo_listfreqs.count() > 0:
                    self.mainWidget.qcombo_listfreqs.removeItem(0)
                    # print self.mainWidget.qcombo_listfreqs.count, "del"
                self.frequenze = []
                for f in freqs:
                    self.mainWidget.qcombo_listfreqs.addItem(f[:-7] + "." + f[-7:-1] + " MHz")
                    self.frequenze += [f[:-1]]
                # print self.frequenze
            except:
                self.mainWidget.qtext_listfreqs.setText("")
                self.mainWidget.qtext_listfreqs.append("Not a valid file!")
                pass
        else:
            self.mainWidget.qtext_listfreqs.setText("")
            self.mainWidget.qtext_listfreqs.append("Please select the frequencies file!")

    def select_fpga_firmware(self):
        # print "Select Firmware"
        fpga_fw_file = easygui.fileopenbox(msg='Please select the bitstream file', default="../bitstream/*")
        if not fpga_fw_file == None:
            self.mainWidget.qtext_adu_fw.setText(fpga_fw_file)


if __name__ == "__main__":
    os.system("python ../config/setup.py")
    app = QtGui.QApplication(sys.argv)
    window = iTPM("tpm_test.ui")

    window.housekeeping_signal.connect(window.updateHK)
    window.jig_pm_signal.connect(window.updateJIGpm)
    window.antenna_test_signal.connect(window.updateAntennaTest)

    sys.exit(app.exec_())

    # tpm_preadu.preaduWindow(self.tpms[tpm]['TPM'], self.subrack['srconfig'][tpm]
