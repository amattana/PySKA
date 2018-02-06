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


from matplotlib import pyplot as plt
import struct,os,glob
from optparse import OptionParser
import numpy as np
from tpm_utils import *

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

    parser.add_option("-r", "--recursive", action="store_true",
                      dest="recursive",
                      default=False,
                      help="Do it recursively")

    (options, args) = parser.parse_args()
    
    plt.ioff()

    if options.spe_file=="" or not os.path.isfile(options.spe_file):
        d=options.directory
        if not d[-1]=="/":
            d = d + "/"
        if os.path.isdir(d) and options.recursive: 
            if not os.path.exists(d+"images"):
                os.makedirs(d+"images")
            TPMs = glob.glob(d+"10*")
            for tpm in TPMs:
                for rx in range(1,17):
                    for pol in ["X","Y"]:
                        data_path = tpm + "/RX-" + str("%02d" % (rx)) + "/Pol-" + pol + "/"
                        files = glob.glob(data_path+"*tdd")
                        if len(files)>0:
                            with open(files[0],"r") as f:
                                a=f.read()
                            l = struct.unpack(">d",a[0:8])[0]
                            data=struct.unpack(">"+str(int(l))+"d",a[8:])
                            singolo = calcSpectra(data)
                            singoli=np.zeros(len(singolo))
                            singoli[:] += singolo
                        else:
                            print "Empty directory:",data_path
                        if len(files)>1:
                            print "Averaging",len(files),"spectra for dir:",data_path
                            for fl in files[1:]:
                                with open(fl,"r") as f:
                                    a=f.read()
                                l = struct.unpack(">d",a[0:8])[0]
                                data=struct.unpack(">"+str(int(l))+"d",a[8:])
                                singolo = calcSpectra(data)
                                singoli[:] += singolo
                            singoli /= len(files)
                            plt.plot(np.linspace(0,400,len(singoli[1:])),singoli[1:])
                            plt.xlim(0,400)
                            plt.ylim(-110,-70)
                            plt.title(data_path)
                            plt.savefig(d+"images/"+data_path.replace("/","_")+"avg.png")
                            plt.clf()
                            #plt.show()
                            #exit()
        else:
            print "\n\nError! \n  -  Missing or not existing Directory!"
            print 


