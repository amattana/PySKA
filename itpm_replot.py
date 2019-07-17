#!/usr/bin/env python

'''

  Replot data acquired with itpm_save.py

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2019, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"


import easygui
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec
import glob, struct, sys, os
import numpy as np
from optparse import OptionParser

def readfile(filename):
    with open(filename,"rb") as f:
        vettore = f.read()
    vett=struct.unpack(str(len(vettore))+'b',vettore)
    return vett

def calcSpectra(vett):
    window = np.hanning(len(vett))
    spettro = np.fft.rfft(vett*window)
    N = len(spettro)
    acf = 2  #amplitude correction factor
    spettro[:] = abs((acf*spettro)/N)
    with np.errstate(divide='ignore', invalid='ignore'):
        spettro[:] = 20*np.log10(spettro/127.0)
    return (np.real(spettro))

def plotta_spettro(ax1, spettri, title):
    x = np.linspace(0, 400, len(spettri))
    ax1.set_title(title)
    ax1.plot(x, spettri, color='b')
    ax1.set_ylim([-90, 12])
    ax1.set_xlim([0, 400])
    ax1.set_xlabel("MHz")  # \n\n"+title)
    ax1.set_ylabel("dBm")
    ax1.grid(True)


def worst_other(spettri,hds,r):
    x=xrange(len(spettri))#np.linspace(0,400,len(spettri))
    c=np.concatenate((x,spettri),axis=0).reshape(2,len(x))
    c=[np.delete(c[0],0),np.delete(c[1],0)]
    c=[np.delete(c[0],0),np.delete(c[1],0)]
    c=[np.delete(c[0],0),np.delete(c[1],0)]
    c=[np.delete(c[0],0),np.delete(c[1],0)]
    c=[np.delete(c[0],0),np.delete(c[1],0)]
    c=[np.delete(c[0],0),np.delete(c[1],0)]
    c=[np.delete(c[0],0),np.delete(c[1],0)]
    c=[np.delete(c[0],0),np.delete(c[1],0)]
    c=[np.delete(c[0],0),np.delete(c[1],0)]
    i=0
    while i < range(len(spettri)-1):
        freq = np.where(c[1] == c[1][(int(r[0]/400.*65536)):(int(r[1]/400.*65536))].max())[0][0]
        #print i,max(c[1]),c[0][freq],c[1][freq]
        #print "\n",c[0][freq],freq,hds
        if int(c[0][freq]) in hds:
            c=[np.delete(c[0],freq),np.delete(c[1],freq)]
            c=[np.delete(c[0],freq),np.delete(c[1],freq)]
            c=[np.delete(c[0],freq),np.delete(c[1],freq)]
            c=[np.delete(c[0],freq),np.delete(c[1],freq)]
            c=[np.delete(c[0],freq-1),np.delete(c[1],freq-1)]
            c=[np.delete(c[0],freq-2),np.delete(c[1],freq-2)]
            c=[np.delete(c[0],freq-3),np.delete(c[1],freq-3)]
            c=[np.delete(c[0],freq-4),np.delete(c[1],freq-4)]
        else:
            break
        i=i+1
        if i>10:
            break
    return [c[1][freq],(c[0][freq]*400./65536)]
    #ax1.plot(c[0][3000]*400./65536, c[1][freq], color='k', marker="^")

def mark_armonics(ax1,spettri,num):
    freq = np.where(spettri == spettri.max())[0][0]
    hds = []
    for i in range(1,num+1):
        fr = freq*i
        while not (fr < 65536 and fr > 0):
            if fr > 65536:
                fr = 65536 - (fr - 65536)
            if fr < 0:
                fr = -fr
        ax1.plot(fr*400./65536,spettri[fr],color='r',marker='o')
        hds += [fr]
        #print i, freq*i, fr*400./65536,spettri[fr]
        if i == 1 :
            ax1.annotate("Tone", xy=(fr*400./65536, spettri[fr]), xytext=((fr*400./65536)+2, spettri[fr]), fontsize=10)
        else:
            ax1.annotate(str(i), xy=(fr * 400. / 65536, spettri[fr]), xytext=((fr * 400. / 65536)+2, spettri[fr]), fontsize=10)
    return hds

MAP = [["Fiber #1","Y"],
       ["Fiber #1","X"],
       ["Fiber #2","Y"],
       ["Fiber #2","X"],
       ["Fiber #3","Y"],
       ["Fiber #3","X"],
       ["Fiber #4","Y"],
       ["Fiber #4","X"],
       ["Fiber #16","X"],
       ["Fiber #16","Y"],
       ["Fiber #15","X"],
       ["Fiber #15","Y"],
       ["Fiber #14","X"],
       ["Fiber #14","Y"],
       ["Fiber #13","X"],
       ["Fiber #13","Y"],
       ["Fiber #5","Y"],
       ["Fiber #5","X"],
       ["Fiber #6","Y"],
       ["Fiber #6","X"],
       ["Fiber #7","Y"],
       ["Fiber #7","X"],
       ["Fiber #8","Y"],
       ["Fiber #8","X"],
       ["Fiber #12","X"],
       ["Fiber #12","Y"],
       ["Fiber #11","X"],
       ["Fiber #11","Y"],
       ["Fiber #10","X"],
       ["Fiber #10","Y"],
       ["Fiber #9","X"],
       ["Fiber #9","Y"]]


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--scope",
                      action="store_true",
                      dest="scope",
                      default=False,
                      help="Print Single Tone analysys like Spectrum Analyzer")
    (options, args) = parser.parse_args()

    filepath = easygui.fileopenbox(msg='Please select the source files')
    path = filepath[:filepath.rfind("/")+1]
    gs = gridspec.GridSpec(2, 1, height_ratios=[6,1])
    fig = plt.figure(figsize=(9, 6), facecolor='w')
    #plt.ion()
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ch=path.split("/")[-2]
    board=path.split("/")[-3]
    tpm_str = "   TPM Input: " + MAP[int(ch[-2:])][0] + "  Pol-" + MAP[int(ch[-2:])][1]
    title = "Board: #" + board.split(".")[-1] + "  ADU Channel #" + ch[-2:] + ",  " + tpm_str
    l = sorted(glob.glob(path+"*bin"))
    dati = readfile(l[0])
    spettri=np.zeros(len(calcSpectra(dati)))
    print ""
    for f in l:
        dati=readfile(f)
        sys.stdout.write("\rProcessing file: " +f)
        sys.stdout.flush()
        spettri[:] += calcSpectra(dati)
    spettri /= len(l)
    spettri += 10
    ax1.cla()
    plotta_spettro(ax1,spettri,title)
    ax2.cla()
    ax2.plot(range(100), color='w')
    ax2.set_axis_off()

    if options.scope:
        ax1.plot(np.zeros(400) + 6, color='r', linestyle="--")
        ax1.plot(np.zeros(400) - 6, color='r', linestyle="--")
        ax1.annotate("Gain High Limit", xy=(200, 7), xytext=(202, 7), color='r', fontsize=10)
        ax1.annotate("Gain Low Limit", xy=(200, -10), xytext=(202, -9.5), color='r', fontsize=10)

        hds = mark_armonics(ax1,spettri,10)

        wo = worst_other(spettri, hds, (50,350))
        if hds[0]>17800:
            ct = worst_other(spettri, hds, (105.8,106))
        else:
            ct = worst_other(spettri, hds, (111.5,111.7))

        if not os.path.isdir("images"):
            os.makedirs("images")
        ax2.cla()
        ax2.plot(range(100),color='w')
        ax2.set_axis_off()
        tone_freq = "%f"%(hds[0]*400./65536)
        tone_freq = tone_freq[:7]+"."+tone_freq[7:]

        ax1.annotate("Total Gain: "+"%3.1f"%(60+spettri[hds[0]])+" dB",(151,-19),fontsize=12)

        ax2.annotate("Foundamental Tone: "+"%3.1f"%(spettri[hds[0]])+" dBm",(1,82),fontsize=12)
        ax2.annotate("Second Harmonic: "+"%3.1f"%(spettri[hds[1]])+" dBm",(1,42),fontsize=12)
        ax2.annotate("Third Harmonic: "+"%3.1f"%(spettri[hds[2]])+" dBm",(1,2),fontsize=12)

        ax2.annotate("Tone Frequency: "+tone_freq+" Hz",(40,82),fontsize=12)

        ax2.annotate("Cross Talk: "+"%3.1f"%(spettri[hds[0]]-ct[0])+" dBC @ "+"%6.3f"%(ct[1])+" MHz",(40,2),fontsize=12)
        ax1.plot(ct[1]-1, ct[0]-1, color='y', marker="o")
        ax1.annotate("CT", xy=(ct[1] - 10, ct[0]+2), xytext=(ct[1] - 10, ct[0]+2), fontsize=9)

        ax2.annotate("Worst Other: "+"%3.1f"%(wo[0])+" dBm  @ "+"%6.3f"%(wo[1])+" MHz",(40,42),fontsize=12)
        ax1.plot(wo[1], wo[0], color='g', marker="^")
        ax1.annotate("WO", xy=(wo[1] + 3, wo[0]), xytext=(wo[1] + 3, wo[0]), fontsize=9)

    else:

        adu_rms = np.sqrt(np.mean(np.power(dati, 2), 0))
        volt_rms = adu_rms * (1.7 / 256.)  # VppADC9680/2^bits * ADU_RMS
        power_adc = 10 * np.log10(
            np.power(volt_rms, 2) / 400.) + 30  # 10*log10(Vrms^2/Rin) in dBWatt, +3 decadi per dBm
        power_rf = power_adc + 12  # single ended to diff net loose 12 dBm

        ax2.annotate("Total Power: %3.1f dBm" % power_rf, (40, 82), fontsize=12)

    plt.tight_layout()
    plt.show()

    sys.stdout.write("\rDirectory processed: " +  path+ "                       \n")
    sys.stdout.flush()
