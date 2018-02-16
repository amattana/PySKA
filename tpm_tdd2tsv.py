import numpy as np
from tpm_utils import *
import struct
from optparse import OptionParser

def tdd2tsv(fl):
    with open(fl,"r") as f:
        d=f.read()
    l = struct.unpack(">d",d[0:8])[0]
    data=struct.unpack(">"+str(int(l))+"d",d[8:])
    singolo = calcSpectra(data)
    f=open(fl[:-3]+"csv","w")
    for i in xrange(len(singolo)):
        f.write("%12.9f\t%6.3f\n"%(a[i],singolo[i]))
    f.close()


if __name__ == "__main__":
    parser = OptionParser()
    
    parser.add_option("-f", "--spe_file",
                      dest="tdd_file",
                      default="",
                      help="Input Time domain File '.tdd' saved using tpm_dump.py")

    (options, args) = parser.parse_args()

    if os.path.isfile(options.tdd_file):
        print("\n\nReading file:"+options.tdd_file)
        tdd2tsv(options.tdd_file)
        print("\n\nWritten file: "+options.tdd_file[:-3]+"tsv")
        print("\n\nExecution terminated")
    else:
        print("\n\nThe given file does not exist!!\n\n")


