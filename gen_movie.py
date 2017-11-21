import sys

sys.path.append("../board")
sys.path.append("../rf_jig")
sys.path.append("../config")
sys.path.append("../repo_utils")
from tpm_utils import *
from bsp.tpm import *

DEVNULL = open(os.devnull, 'w')

import matplotlib.pyplot as plt

import urllib3

# Test application, security unimportant:
urllib3.disable_warnings()

# Other stuff
import numpy as np
import datetime

# Some globals
COLONNE = 20
RIGHE = 256
COLORS = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
OUT_PATH = "/data/data_2/2017-11-AAVS-FIX/2017-11-16/"
MAP_PATH = "Maps"
MOVIE_FOLDER = "Videos"
PATH_PLOT_LIST = "./.plotlists/"
EX_FILE = "/home/mattana/Downloads/AAVS 1.1 Locations and connections.xlsx"
EX_FILE_AAVS = "/home/aavs/Downloads/AAVS 1.1 Locations and connections.xlsx"


def plot_map(ant, marker='o', markersize=12, color='g', print_name=False):
    x = [float(str(a['East']).replace(",", ".")) for a in ant]
    y = [float(str(a['North']).replace(",", ".")) for a in ant]
    # name = [a['Hybrid Cable'] for a in ant]
    name = [a['Base'] for a in ant]
    ax.plot(x, y, marker=marker, markersize=markersize, linestyle='None', color=color)
    if print_name:
        for i in range(len(name)):
            # ax.annotate("%s"%name[i], xy=(x[i],y[i]), fontsize=10, fontweight='bold')
            ax.annotate("%d" % name[i], xy=(x[i], y[i]), fontsize=10, fontweight='bold')


def plotta(dati, fname, pol):
    if pol == "X" or pol == 0:
        plt.plot(np.linspace(0, 400, len(dati[1:])), dati[1:], color='b')
    else:
        plt.plot(np.linspace(0, 400, len(dati[1:])), dati[1:], color='g')
    plt.xlim(0, 400)
    plt.ylim(-80, -20)
    plt.title(fname[fname.rfind("/") + 1:])
    plt.savefig(fname + ".png")
    plt.clf()


def generateMap(cells, tpm_used, rms_map, timestamp, outdir, mapdir):
    dataora = datetime.datetime.strptime(timestamp, "%Y-%m-%d_%H%M%S")
    for pol in enumerate(["X", "Y"]):
        fig = plt.figure(num=1, figsize=(12, 9), dpi=80, facecolor='w', edgecolor='w')
        ax = fig.add_axes([0.08, 0.08, 0.7, 0.85])
        ax.set_title("AAVS 1.1 Antennas Map - " + pol[1] + " Pol")

        ax.axis([-25, 25, -25, 25])
        ax.axvline(0, color='b', linestyle='dotted')
        ax.axhline(0, color='b', linestyle='dotted')

        ax.plot([-7.5, 7.5], [20, -20], linestyle='dotted', color='b')
        ax.plot([-19, 19], [20, -20], linestyle='dotted', color='b')
        ax.plot([-20, 20], [8, -8], linestyle='dotted', color='b')
        ax.plot([-20, 20], [-7, 7], linestyle='dotted', color='b')
        ax.plot([-7.5, 7.5], [-20, 20], linestyle='dotted', color='b')
        ax.plot([-19, 19], [-20, 20], linestyle='dotted', color='b')

        ax.annotate("TPM-1", xy=(19, 3), fontsize=10)
        ax.annotate("TPM-2", xy=(17, 11), fontsize=10)
        ax.annotate("TPM-3", xy=(10, 18), fontsize=10)
        ax.annotate("TPM-4", xy=(2, 20), fontsize=10)
        ax.annotate("TPM-5", xy=(-5, 20), fontsize=10)
        ax.annotate("TPM-6", xy=(-13, 18), fontsize=10)
        ax.annotate("TPM-7", xy=(-20, 11), fontsize=10)
        ax.annotate("TPM-8", xy=(-22, 3), fontsize=10)
        ax.annotate("TPM-9", xy=(-22, -4), fontsize=10)
        ax.annotate("TPM-15", xy=(-20, -12), fontsize=10)
        ax.annotate("TPM-14", xy=(-13, -18), fontsize=10)
        ax.annotate("TPM-13", xy=(-5, -21), fontsize=10)
        ax.annotate("TPM-12", xy=(2, -21), fontsize=10)
        ax.annotate("TPM-11", xy=(10, -18), fontsize=10)
        ax.annotate("TPM-10", xy=(17, -12), fontsize=10)
        ax.annotate("TPM-9", xy=(19, -4), fontsize=10)

        ax.annotate("NORTH", xy=(-2, 22), fontweight='bold', fontsize=9)
        ax.annotate("SOUTH", xy=(-1.9, -24), fontweight='bold', fontsize=9)
        ax.annotate("EAST", xy=(21.5, 0), fontweight='bold', fontsize=9)
        ax.annotate("WEST", xy=(-24.5, 0), fontweight='bold', fontsize=9)
        ax.text(-8, -28.5, datetime.datetime.strftime(dataora, "%Y/%m/%d %H:%M:%S UTC"), fontsize=16)
        print len(rms_map)
        print len(rms_map)
        for tpm in range(1, tpm_used):
            # print tpm, " * "
            rms = [a for a in rms_map if a[0] == "10.0.10." + str(tpm)]
            if rms == []:
                continue
            rms = rms[0]
            for rx in range(1, 16 + 1):
                cella = [a for a in cells if ((a['TPM'] == tpm) and (a['RX'] == rx))]
                if not cella == []:
                    x = cella[0]['East']
                    y = cella[0]['North']
                    ax.plot(x, y, marker='8', markersize=10, linestyle='None',
                            color=rms_color(rms[1][((rx - 1) * 2) + pol[0]]))
        plt.draw()
        plt.savefig(outdir + mapdir + "/Pol-" + pol[1] + "/AAVS1_MAP_Pol-" + pol[1] + timestamp + ".png")
        plt.close()

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-d", "--data",
                      dest="data",
                      default="2017-11-20",
                      help="Date of data to be reprocessed (YYYY-MM-DD)")


    (options, args) = parser.parse_args()


    OUT_PATH="/data/data_2/2017-11-AAVS-FIX/" + options.data + "/"

    plt.ion()
    TPMs = ['10.0.10.{0}'.format(i+1) for i in xrange(16)]

    for tpm in TPMs:
        for rx in range(1,17):
            for pol in ["X","Y"]:
                data_path = OUT_PATH + tpm + "/RX-" + str("%02d" % (rx)) + "/Pol-" + pol
                if os.path.exists(data_path):
                    fname = "TPM-" + str("%02d" % (int(tpm.split(".")[-1]))) + "_RX-" + str("%02d" % (rx)) + "_Pol-" + pol + ".avi"
                    print "\n\nGenerating movie for " + fname
                    os.system("rm -rf " +  OUT_PATH + MOVIE_FOLDER + "/Pol-" + pol + "/" + fname)
                    cmd = "ffmpeg -f image2 -i " + data_path + "/%*.png  " + OUT_PATH + MOVIE_FOLDER + "/Pol-" + pol + "/" + fname
                    print "\n",cmd,"\n\n"
                    os.system(cmd)






