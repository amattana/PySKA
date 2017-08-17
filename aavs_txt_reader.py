import numpy as np
from matplotlib import pyplot as pl

if __name__=="__main__":
    from optparse import OptionParser
    import sys

    #command line parsing
    op = OptionParser()
    op.add_option("-f", "--fname", dest="fname", type="str", default="", help="The name of the file to be plotted")
    opts, args = op.parse_args(sys.argv[1:])


    a=open(opts.fname)
    data=a.readlines()
    a.close()

    dati=[]
    for i in range(len(data)):                                  
        dati += [[data[i][:-1].split("\t")]]

    trasposta=np.transpose(dati)
    x=trasposta[0][0]
    for i in range(16):                                         
        pl.plot(x, trasposta[i+1][0])
    pl.show()
