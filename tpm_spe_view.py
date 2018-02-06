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
import struct,os
from optparse import OptionParser

if __name__ == "__main__":
    parser = OptionParser()
    
    parser.add_option("-f", "--spe_file",
                      dest="spe_file",
                      default="",
                      help="Input Spectra fle '.spe' saved using tpm_dump.py")

    (options, args) = parser.parse_args()

    if options.spe_file=="" or not os.path.isfile(options.spe_file):
        print "\n\nError! \n  -  Missing input file or the given file does not exist."
        print "\nUsage: ./tpm_spe_view.py -f filename.spe\n"
    else:
        with open(options.spe_file,"r") as f:
            a=f.read()
        l = struct.unpack(">d",a[0:8])[0]
        data=struct.unpack(">"+str(int(l))+"d",a[8:])
        plt.plot(xrange(len(data)),data)
        plt.xlim(1,len(data)-1)
        plt.show()


