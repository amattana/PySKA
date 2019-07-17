#!/usr/bin/env python

'''

   TPM Spectra Viever 

   Used to plot spectra saved using tpm_dump.py

'''

__copyright__ = "Copyright 2018, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"


#from __future__ import division
from matplotlib import pyplot as plt
import struct,os,glob
from optparse import OptionParser
import numpy as np
from datetime import datetime, timedelta

def calcSpectrum(vett):
    window = np.hanning(len(vett))
    spettro = np.fft.rfft(vett*window)
    N = len(spettro)
    acf = 2  #amplitude correction factor
    spettro[:] = abs((acf*spettro)/N)
    return (np.real(spettro))

def calcSpectra(vett, nsample):
    #window = np.hanning(nsample)
    #spettro = []
    sp=[vett[a:a+nsample] for a in xrange(0, len(vett), nsample)]
    singoli=np.zeros(len(calcSpectrum(sp[0])))
    for k in sp:
        singolo = calcSpectrum(k)
        singoli[:] += singolo
    singoli[:] /= (2**17/nsample) # federico
    #spettro += [singoli]
    spettro = np.array(singoli)
    with np.errstate(divide='ignore', invalid='ignore'):
        result = 20*np.log10(spettro/127.0)
    return result


def calc_dbm(data):
    dati=np.array(data,dtype=np.float64)
    adu_rms = np.sqrt(np.mean(np.power(dati,2),0))
    volt_rms = adu_rms * (1.7/256.)
    power_adc = 10*np.log10(np.power(volt_rms,2)/400.)+30
    power_rf = power_adc + 12
    return power_rf

def totimestamp(dt, epoch=datetime(1970,1,1)):
    td = dt - epoch
    # return td.total_seconds()
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6

if __name__ == "__main__":
    parser = OptionParser()
    
    parser.add_option("-f", "--file",
                      dest="spe_file",
                      default="",
                      help="Input Time Domain Data file '.tdd' saved using tpm_dump.py")

    parser.add_option("-d", "--directory",
                      dest="directory",
                      default="",
                      help="Directory containing '.tdd' files to be averaged")

    (options, args) = parser.parse_args()
    
    
    if options.spe_file=="" or not os.path.isfile(options.spe_file):
        d=options.directory
        if not d[-1]=="/":
            d = d + "/"
        if os.path.isdir(d): 
            MEAS = sorted(glob.glob(d+"*tdd"))
            val = []
            max_adc = []
            x = []
            spettri = []
            #pylab.ion()
            fig, (ax1, ax2, ax3) = plt.subplots(nrows=3, figsize=(7, 9.6))

            for meas in MEAS:
                with open(meas,"r") as f:
                    a=f.read()
                l = struct.unpack(">d",a[0:8])[0]
                data=struct.unpack(">"+str(int(l))+"d",a[8:])
                val += [calc_dbm(data)]
                max_adc += [max(data)]
                spettri += [calcSpectra(data, 1024)]
                x += [totimestamp(datetime.strptime(meas[meas.rfind("/")+1+28:-4],"%Y-%m-%d_%H%M%S"))]
                #ax3.imshow(np.transpose(calcSpectra(data, 1024)), interpolation='none', aspect='auto', extent=[0,len(max_adc),400,0])

                
            ax1.plot(x,np.zeros(len(max_adc))+127, color='r')
            #ax1.plot(x,np.zeros(len(max_adc))+127, color='r', linestyle=None, marker=".")

            ax1.plot(x,max_adc, color='b', linestyle="None", marker=".")
            ax1.set_xlim([x[0],x[-1]])
            ax1.set_ylim([0,150])
            ax1.set_title("ADC Raw Values (Clipping)")
            ax1.set_xlabel('Samples (time)')
            ax1.set_ylabel("ADC Counts")
            ax1.grid(True)

            ax2.plot(x,val, linestyle="None", marker=".")
            ax2.set_xlim([x[0],x[-1]])

            #print len(val), len(min_adc), len(spettri), len(spettri[0])
            ax2.set_title("RF Power measured by ADC")
            ax2.set_xlabel('Samples (time)')
            ax2.set_ylabel("RF Power (dBm)")
            ax2.grid(True)

            ax3.imshow(np.transpose(spettri), interpolation='none', aspect='auto', extent=[0,len(max_adc),400,0])
            ax3.set_xlim([0,len(max_adc)])
            ax3.set_title("Spectrogram")
            ax3.set_xlabel('Spectra (time)')
            ax3.set_ylabel("MHz")
            plt.tight_layout()
            plt.show()
            #a=raw_input("Program terminated, type a char to end")
            #sys.exit()
    else:
        print "\n\nInvalid Directory!"

