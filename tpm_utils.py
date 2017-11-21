import sys,struct,os,time,socket
sys.path.append("..\\")
sys.path.append("..\\..\\")
sys.path.append("../board")
sys.path.append("../rf_jig")
sys.path.append("../config")
sys.path.append("../repo_utils")
from PyQt4 import QtCore, QtGui
import numpy as np
from netproto.sdp_medicina import sdp_medicina as sdp_med
from struct import *
import manager as config_man
from bsp.tpm import *



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

def read_preadu_regs(Tpm):
    reg_values  = Tpm.bsp.preadu_rd128(0)
    reg_values += Tpm.bsp.preadu_rd128(1)
    return reg_values


def write_preadu_regs(Tpm, conf):
    Tpm.bsp.preadu_wr128(0,conf[0:4])
    time.sleep(0.2)
    Tpm.bsp.preadu_wr128(1,conf[4:8])
    time.sleep(0.2)
    reg_values  = Tpm.bsp.preadu_rd128(0)
    time.sleep(0.2)
    reg_values += Tpm.bsp.preadu_rd128(1)
    return reg_values
    
def tpm_obj(loc_ip):
    tpm = {}
    tpm['TPM'] = TPM(ip=loc_ip, port=10000, timeout=1)
    tpm['IP']  = loc_ip
    return tpm

def snapTPM(tpm, debug=False):
    try:
        if not debug:
            UDP_PORT = 0x1234 + int(tpm['IP'].split(".")[-1])
            done = 0
            sdp = sdp_med(UDP_PORT)
            misure = []
            snap =  sdp.reassemble()
            channel_id_list = snap[4:4+int(snap[3])]
            channel_list = snap[4+int(snap[3]):]
            m = 0
            dati = []
            for n in range(len(channel_id_list)):
                if channel_id_list[n] == "1":
                    dati += [channel_list[m]]
                    m += 1
       		misure += [dati]
            del sdp
            del dati
            del channel_list
            return misure
        else:
            f=open("data_stored","r")
            b=[[]]
            for i in range(32):
                b[0] += [unpack(">"+str(2**17)+"b",f.read(2**17))]
            f.close()
            return(np.array(b))
    except:
        print "Unable to snap data!"
        pass

def rms_color(w):
    if w<5:
        return "#0000ff"
    elif w<10:
        return "#00c5ff"
    elif w<15:
        return "#00ffc5"
    elif w<20:
        return "#22ff00"
    elif w<25:
        return "#ff9f00"
    elif w<30:
        return "#ff1d00"
    else:
        return "#c800c8"

def calcFreqs(lenvett, sample_rate):
    x = np.arange(0,lenvett,1)
    freqs = np.fft.rfftfreq(x.shape[-1])
    freqs[:] = freqs*sample_rate    # modificato
    return freqs

def calcSpectra(vett):
    window = np.hanning(len(vett))
    spettro = np.fft.rfft(vett*window)
    N = len(spettro)
    acf = 2  #amplitude correction factor
    spettro[:] = abs((acf*spettro)/N)
    with np.errstate(divide='ignore', invalid='ignore'):
        spettro[:] = 20*np.log10(spettro/127.0)
    return (np.real(spettro))

def get_raw_meas(objtpm, nsamples=1024,debug=False):
    '''
    Get acquisition from TPM
    :param objtpm: a TPM object (can generated it by using tpm_obj(ip))
    :param nsamples=1024: input for the FFT, will return nsample/2 FFT bins
    :param debug=Fasle: If true do not acquire from TPM but use data stored in a file
    :return: freqs, spettro, np.array(dati,dtype=np.float64)[32], adu_rms[32], power_rf[32]
    '''
    i=debug
    TPM_ADU_REMAP=[1,0,3,2,5,4,7,6,17,16,19,18,21,20,23,22,30,31,28,29,26,27,24,25,14,15,12,13,10,11,8,9]
    sample_rate=800
    dati=snapTPM(objtpm, debug=i)[0]
    dati=[dati[k] for k in TPM_ADU_REMAP]
#    print "SNAP LEN:",len(dati)
    spettro = []
    #freqs=calcFreqs(len(dati[0])/16, sample_rate) # originale
    freqs=calcFreqs(len(dati[0])/(2**17/nsamples), sample_rate) # aavs1 federico
    #n=8192 # split and average number, from 128k to 16 of 8k # originale
    n=nsamples # split and average number, from 128k to 16 of 8k # aavs1 federico
    for i in xrange(32):
        l=dati[i]
#        print "ADU Input: ",i,"Remapped in ",TPM_ADU_REMAP[i], "Len: ", len(l)
        sp=[l[TPM_ADU_REMAP[i]:TPM_ADU_REMAP[i] + n] for TPM_ADU_REMAP[i] in xrange(0, len(l), n)]
        singoli=np.zeros(len(calcSpectra(sp[0])))
        for k in sp:
            singolo = calcSpectra(k)
            singoli[:] += singolo
        #singoli[:] /= 16 # originale
        singoli[:] /= (2**17/nsamples) # federico
        spettro += [singoli]
    dati=np.array(dati,dtype=np.float64)

    adu_rms = np.zeros(32)
    adu_rms = adu_rms + np.sqrt(np.mean(np.power(dati,2),1))

    volt_rms = adu_rms * (1.7/256.)                           # VppADC9680/2^bits * ADU_RMS
    power_adc = 10*np.log10(np.power(volt_rms,2)/400.)+30     # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
    power_rf = power_adc + 12                                 # single ended to diff net loose 12 dBm
    return freqs, spettro, np.array(dati,dtype=np.float64), adu_rms, power_rf

#self.freqs, self.spettro_mediato, self.dati = get_raw_meas(objtpm, meas="SPECTRA")
#freqs=self.calcFreqs(len(data))     
#spettro = self.plot_spectra(data)
#self.matlabPlotACQ.plotCurve(freqs, spettro, yAxisRange = [-100,0],title=self.mainWidget.qcombo_adu_channel.currentText(), xLabel="MHz", yLabel="dBFS", plotLog=True)

#for i in xrange(32):
#    if i%32%2==0:   # solo pari
#        plotcolor="b"
#    else:
#        plotcolor="g"
#    self.miniPlots.plotCurve(self.freqs, self.spettro_mediato[i], i/2, yAxisRange = [-100,0], title="ANT "+str(i+1), xLabel="MHz", yLabel="dBFS", plotLog=True, colore=plotcolor) 

def programming_cplds(da,a):
    for i in xrange(da,a+1):
        print "\n\n#################################################"
        print "\nDownloading CPLD Firmware of TPM # ",i
        os.system("python cpld_fw_write.py -f /home/mattana/cpld_v250117b0_rb.bit --ip=10.0.10."+str(i))
        print "\nTPM # ",i, " done!"
        time.sleep(2)

def configure_tpms(da,a):
    for i in xrange(da,a+1):
    print "\n\n#################################################"
    os.system("python test.py -f 800 -i 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31 -s --ip=10.0.10."+str(i))
        print "\nTPM # ",i, " done!"
        time.sleep(2)

def programming_fpgas(da,a):
    for i in xrange(da,a+1):
        print "\n\n#################################################"
        print "\nDownloading Xilinx Firmware of TPM # ",i
        os.system("python fpga_prog.py -f ../bitstream/itpm_v1_1_tpm_test_wrap_test31.bit --ip=10.0.10."+str(i))                         print "\nTPM # ",i, " done!"
        time.sleep(2)

