#!/usr/bin/python2.7

import os,sys
from tpm_utils import *
sys.path.append("../board")
sys.path.append("../rf_jig")
sys.path.append("../config")
sys.path.append("../repo_utils")
from bsp.tpm import *
import numpy as np
import subprocess
DEVNULL = open(os.devnull,'w')

def tpm_obj(loc_ip):
    tpm = {}
    tpm['TPM'] = TPM(ip=loc_ip, port=10000, timeout=1)
    tpm['IP']  = loc_ip
    return tpm

def calcFreqs(lenvett):
    x = np.arange(0,lenvett,1)
    freqs = np.fft.rfftfreq(x.shape[-1])
    freqs[:] = freqs*sample_rate    # modificato
    return freqs

def plot_spectra(vett):
    #spettro=np.zeros(len(vett)/2) # rem 1
    #print "Doing spectrum of ", len(vett), "samples"
    window = np.hanning(len(vett))
    #print "Windowing"
    spettro = np.fft.rfft(vett*window) # vedere se spettro[:]= accelera
    #print "Computed Spectrum"
    N = len(spettro)
    acf = 2  #amplitude correction factor
    spettro[:] = abs((acf*spettro)/N)
    spettro[:] = 20*np.log10(spettro/127.0)
    #dB_FS = 10*log10(sum(abs(time_data(:,(n_time_record*(m-1))+1)).^2)/size(time_data(:,(n_time_record*(m-1))+1),1))-10*log10(0.5);
    #print "End of subroutine"
    return (np.real(spettro))


def snapTPM(tpm):
	try:
		UDP_PORT = 0x1234 + int(tpm['IP'].split(".")[-1])
		done = 0
		sdp = sdp_med(UDP_PORT)
		misure = []
		#while(done != num or num == 0):
		snap =  sdp.reassemble()
		channel_id_list = snap[4:4+int(snap[3])]
		channel_list = snap[4+int(snap[3]):]

		#done += 1
		#sys.stdout.write("\rAcq # %d/%d " %(done,num))
		#sys.stdout.flush()
		m = 0
		dati = []
		for n in range(len(channel_id_list)):
			if channel_id_list[n] == "1":
					#last_filename=save_raw(path, channel_list[m],n,done)
				dati += [channel_list[m]]
					#print len(data)
				m += 1
		misure += [dati]
		del sdp
		del dati
		del channel_list
		#?print 
		return misure
	except:
		print "Unable to snap data!"
		pass

TPMs=['10.0.10.2', '10.0.10.3', '10.0.10.4', '10.0.10.5', '10.0.10.6', '10.0.10.25']
remap=[1,0,3,2,5,4,7,6,17,16,19,18,21,20,23,22,30,31,28,29,26,27,24,25,14,15,12,13,10,11,8,9]
tpms = []
for i in range(len(TPMs)):
    tpms += [tpm_obj(TPMs[i])]
print

sample_rate=800
dati=snapTPM(tpms[0])[0]
spettro = []
freqs=calcFreqs(len(dati[0])/16)
n=8192 # split and average number, from 128k to 16 of 8k
for i in xrange(32):
    l=dati[remap[i]]
    sp=[l[remap[i]:remap[i] + n] for remap[i] in xrange(0, len(l), n)]
    singoli=np.zeros(len(plot_spectra(sp[0])))
    for k in sp:
        singolo = plot_spectra(k)
        singoli[:] += singolo
    singoli[:] /= 16      
    spettro += [singoli]

dati=np.array(dati,dtype=np.float64)
#return freqs, spettro, np.array(dati,dtype=np.float64)

adu_rms = np.zeros(32)
adu_rms = adu_rms + np.sqrt(np.mean(np.power(dati,2),1))
volt_rms = adu_rms * (1.7/256.)                           # VppADC9680/2^bits * ADU_RMS
power_adc = 10*np.log10(np.power(volt_rms,2)/400.)+30     # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
power_rf = power_adc + 12                                 # single ended to diff net loose 12 dBm

print "    ( POL-X, POL-Y)   ( POL-X, POL-Y)   ( POL-X, POL-Y)   ( POL-X, POL-Y)"
print "  -------------------------------------------------------------------------"    
for i in range(4):
    print "    ( % 5.1f, % 5.1f)   ( % 5.1f, % 5.1f)   ( % 5.1f, % 5.1f)   ( % 5.1f, % 5.1f)"%(po
wer_rf[i*8],power_rf[1+i*8],power_rf[2+i*8],power_rf[3+i*8],power_rf[4+i*8],power_rf[5+i*8],power
_rf[6+i*8],power_rf[7+i*8])
print


