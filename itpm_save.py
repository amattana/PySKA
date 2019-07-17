#!/usr/bin/env python

'''

  Dump data from a specific TPM input

'''

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2018, Istituto di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

import visa
import os, sys, glob
import easygui
import time, datetime
from optparse import OptionParser
import numpy as np
import socket
from struct import *

sys.path.append("../board")
sys.path.append("../board/netproto")
sys.path.append("../rf_jig")
from netproto.sdp_medicina import sdp_medicina as sdp_med
from tpm_utils import *
# from qt_rf_jig_utils import *
from SMY02 import RS_SMY02
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec


def readfile(filename):
    with open(filename, "rb") as f:
        vettore = f.read()
    vett = struct.unpack(str(len(vettore)) + 'b', vettore)
    return vett


def calcSpectra(vett):
    window = np.hanning(len(vett))
    spettro = np.fft.rfft(vett * window)
    N = len(spettro)
    acf = 2  # amplitude correction factor
    spettro[:] = abs((acf * spettro) / N)
    with np.errstate(divide='ignore', invalid='ignore'):
        spettro[:] = 20 * np.log10(spettro / 127.0)
    return (np.real(spettro))


def mark_armonics(ax1, spettri, num):
    freq = np.where(spettri == spettri.max())[0][0]
    hds = []
    for i in range(1, num + 1):
        fr = freq * i
        while not (fr < 65536 and fr > 0):
            if fr > 65536:
                fr = 65536 - (fr - 65536)
            if fr < 0:
                fr = -fr
        ax1.plot(fr * 400. / 65536, spettri[fr], color='r', marker='o')
        hds += [fr]
        # print i, freq*i, fr*400./65536,spettri[fr]
        if i == 1:
            ax1.annotate("Tone", xy=(fr * 400. / 65536, spettri[fr]), xytext=((fr * 400. / 65536) + 2, spettri[fr]),
                         fontsize=10)
        else:
            ax1.annotate(str(i), xy=(fr * 400. / 65536, spettri[fr]), xytext=((fr * 400. / 65536) + 2, spettri[fr]),
                         fontsize=10)
    return hds


def plotta_spettro(ax1, spettri, title):
    x = np.linspace(0, 400, len(spettri))
    ax1.set_title(title)
    ax1.plot(x, spettri, color='b')
    ax1.set_ylim([-90, 12])
    ax1.set_xlim([0, 400])
    ax1.set_xlabel("MHz")  # \n\n"+title)
    ax1.set_ylabel("dBm")
    ax1.grid(True)


def worst_other(spettri, hds, r):
    x = xrange(len(spettri))  # np.linspace(0,400,len(spettri))
    c = np.concatenate((x, spettri), axis=0).reshape(2, len(x))
    c = [np.delete(c[0], 0), np.delete(c[1], 0)]
    c = [np.delete(c[0], 0), np.delete(c[1], 0)]
    c = [np.delete(c[0], 0), np.delete(c[1], 0)]
    c = [np.delete(c[0], 0), np.delete(c[1], 0)]
    c = [np.delete(c[0], 0), np.delete(c[1], 0)]
    c = [np.delete(c[0], 0), np.delete(c[1], 0)]
    c = [np.delete(c[0], 0), np.delete(c[1], 0)]
    c = [np.delete(c[0], 0), np.delete(c[1], 0)]
    c = [np.delete(c[0], 0), np.delete(c[1], 0)]
    i = 0
    while i < range(len(spettri) - 1):
        freq = np.where(c[1] == c[1][(int(r[0] / 400. * 65536)):(int(r[1] / 400. * 65536))].max())[0][0]
        # print i,max(c[1]),c[0][freq],c[1][freq]
        # print "\n",c[0][freq],freq,hds
        if int(c[0][freq]) in hds:
            c = [np.delete(c[0], freq), np.delete(c[1], freq)]
            c = [np.delete(c[0], freq), np.delete(c[1], freq)]
            c = [np.delete(c[0], freq), np.delete(c[1], freq)]
            c = [np.delete(c[0], freq), np.delete(c[1], freq)]
            c = [np.delete(c[0], freq - 1), np.delete(c[1], freq - 1)]
            c = [np.delete(c[0], freq - 2), np.delete(c[1], freq - 2)]
            c = [np.delete(c[0], freq - 3), np.delete(c[1], freq - 3)]
            c = [np.delete(c[0], freq - 4), np.delete(c[1], freq - 4)]
        else:
            break
        i = i + 1
        if i > 10:
            break
    return [c[1][freq], (c[0][freq] * 400. / 65536)]


# ax1.plot(c[0][3000]*400./65536, c[1][freq], color='k', marker="^")

def eq_retta(x1, y1, x2, y2):
    m = float(y2 - y1) / (x2 - x1)
    q = y1 - (m * x1)

    def retta(x):
        return m * x + q

    return retta


def cpl_att(cpl_curve, freq_set):
    # print freq_set
    for i in range(len(cpl_curve)):
        if cpl_curve[i][0] > freqset:
            break
    if i > 0:
        r = eq_retta(cpl_curve[i][0], cpl_curve[i][1], cpl_curve[i - 1][0], cpl_curve[i - 1][1])
    else:
        r = eq_retta(cpl_curve[0][0], cpl_curve[0][1], cpl_curve[1][0], cpl_curve[1][1])
    return r(freqset)


def read_cpl_curve(file_cpl):
    cpl_curve = []
    f_cpl = open(file_cpl, 'r')
    cpl_list = f_cpl.readlines()
    for i in range(len(cpl_list)):
        # print cpl_list[i][:-1].split()
        cpl_curve += [[int(cpl_list[i].split()[0]), float(cpl_list[i].split()[2])]]
    # print cpl_curve[i]
    # cpl_curve[i][0] = int(cpl_curve[i][0])
    # cpl_curve[i][0] = float(cpl_curve[i][0])
    f_cpl.close()
    return cpl_curve


def ByteToHex(byteStr):
    # """
    # Convert a byte string to it's hex string representation e.g. for output.
    # """
    return ''.join(["%02X " % ord(x) for x in byteStr]).strip()


def fft(input):
    window = np.blackman(len(input))  # changed from hanning in blackman
    output = np.fft.rfft(input * window)
    N = len(output)
    acf = 2  # amplitude correction factor
    output = abs((acf * output) / N)
    output = 20 * np.log10(output / 128.0)
    return output


def modulo(input):
    output = np.zeros(len(input) / 2, dtype=np.float)
    re = 0.0
    im = 0.0
    for n in range(len(input)):
        if n % 2 == 0:
            re = input[n]
        else:
            im = input[n]
            ##if n % 4 == 1:
            p = (re ** 2 + im ** 2) ** 0.5
            print n
            print re
            print im
            print p
            print
            output[n / 2] = p
    return output


def check_pattern(input):
    seed = input[0]
    for n in range(len(input)):
        recv = input[n] + 128
        if n >= 0 and n <= 11:
            exp = (seed + 128 + n % 4) & 0xFF
        else:
            exp = (seed + 128 + (n - 12)) & 0xFF
        if recv != exp:
            print "error at index " + str(n)
            print "expected " + str(exp)
            print "received " + str(recv)
            xx = pylab.waitforbuttonpress(timeout=0.1)
            exit()
    print "test pattern is good!"


def is_first(channel_id, channel_disable):
    ret = 0
    # print "Partiamo: ",hex(channel_id),hex(channel_disable)
    disable = channel_disable
    # print "disable=",hex(disable)
    for n in range(16):
        # print "if disable=",hex(disable) ,"& 0x1 == 0:" ,hex(disable & 0x1)
        if disable & 0x1 == 0:
            # print "if channel_id == n", hex(channel_id), n
            if channel_id == n:
                ret = 1
            break
        disable = disable >> 1
        # print "disable = disable >> 1", hex(disable)
    # print "RETURN: ", ret
    return ret


def is_last(channel_id, channel_disable):
    ret = 0
    disable = channel_disable
    for n in reversed(range(16)):
        if disable & 0x8000 == 0:
            if channel_id == n:
                ret = 1
            break
        disable = disable << 1
    return ret


def set_channel(channel_ok, channel_id):
    mask = 1 << channel_id
    channel_ok = channel_ok | mask;
    return channel_ok


def save_raw(path, data, chan, seq):
    raw_filename = path + "input_" + str(chan).zfill(2) + "_" + str(seq - 1).zfill(3) + ".bin"
    raw_file = open(raw_filename, "wb")
    raw_file.write(data)
    raw_file.close()
    return raw_filename


MAP = [["Fiber #1", "Y"],
       ["Fiber #1", "X"],
       ["Fiber #2", "Y"],
       ["Fiber #2", "X"],
       ["Fiber #3", "Y"],
       ["Fiber #3", "X"],
       ["Fiber #4", "Y"],
       ["Fiber #4", "X"],
       ["Fiber #16", "X"],
       ["Fiber #16", "Y"],
       ["Fiber #15", "X"],
       ["Fiber #15", "Y"],
       ["Fiber #14", "X"],
       ["Fiber #14", "Y"],
       ["Fiber #13", "X"],
       ["Fiber #13", "Y"],
       ["Fiber #5", "Y"],
       ["Fiber #5", "X"],
       ["Fiber #6", "Y"],
       ["Fiber #6", "X"],
       ["Fiber #7", "Y"],
       ["Fiber #7", "X"],
       ["Fiber #8", "Y"],
       ["Fiber #8", "X"],
       ["Fiber #12", "X"],
       ["Fiber #12", "Y"],
       ["Fiber #11", "X"],
       ["Fiber #11", "Y"],
       ["Fiber #10", "X"],
       ["Fiber #10", "Y"],
       ["Fiber #9", "X"],
       ["Fiber #9", "Y"]]

TARGET_LEVEL = 10.4  # NO ADA
# TARGET_LEVEL = -9.4 # CON ADA
POW_METER_TIMEOUT = 2000
SIG_GEN_MAX_LEVEL = 13

SW_PATH = "D:\\SKA-TPM\\"
DATA_PATH = "2019-07_AAVS1.5_TEST_PREADU/"

GEN_ADDR = 25
POWMETER_ADDR = 14
POWSENSOR_ADDR = 0
SPECTAN_ADDR = 18

HPIB_DB_FILE = "HPIB_DB.txt"
FILE_CPL = "CPL_CURVE.txt"

THIS_UDP_IP = "10.0.10.1"
FPGA_UDP_IP = "10.0.10.2"
UDP_PORT = 0x1236

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--channel",
                      dest="channel",
                      default=0,
                      help="ADC input channel where the signal generator is connected [0 to 31]")
    parser.add_option("-v",
                      action="store_true",
                      dest="verbose",
                      default=False,
                      help="Print lots of many information...")
    parser.add_option("-p",
                      action="store_true",
                      dest="plotta",
                      default=False,
                      help="Plot the last acquisition")
    parser.add_option("-n", "--num",
                      dest="acq_num",
                      default=100,
                      help="Number of acquisition")
    parser.add_option("-b", "--board_ip",
                      dest="board_ip",
                      default="10.0.10.2",
                      help="Board ip, def: 10.0.10.2")
    parser.add_option("--ns",
                      action="store_true",
                      dest="no_sig_gen",
                      default=False,
                      help="do not drive the signal generator (output folder does not append the frequency)")
    parser.add_option("--scope",
                      action="store_true",
                      dest="scope",
                      default=False,
                      help="Print Single Tone analysys like Spectrum Analyzer")
    parser.add_option("--cp",
                      action="store_true",
                      dest="cpl_att",
                      default=False,
                      help="if the power is read from a coupler take into account of its attenuation")
    (options, args) = parser.parse_args()

    if options.cpl_att:
        # print "CPL Correction Factor Enabled"
        cpl_curve = read_cpl_curve(FILE_CPL)
    # print cpl_curve

    if not options.no_sig_gen:
        # Find GPIB plugged devices
        rm = visa.ResourceManager()
        rm_list = rm.list_resources()
        pow_meter = rm.open_resource(u'USB0::0x0957::0x2D18::MY53040009::INSTR')
        pow_meter.timeout = POW_METER_TIMEOUT
        # sig_gen = rm.open_resource(u'GPIB0::25::INSTR')
        sig_gen = RS_SMY02(iec=25)
        supply = rm.open_resource(u'GPIB0::4::INSTR')

        # Read the Input Frequencies File
        print("\nSelect a Frequencies file...")
        freqfile = easygui.fileopenbox(msg='Please select the frequencies file',
                                       default=SW_PATH + 'Freqs\*.txt')
        print("Opening file: %s" % (freqfile))
        freq_file = open(freqfile, 'r')
        freqs = freq_file.readlines()
        print "Found " + str(len(freqs)) + " frequencies!\n"
        freq_file.close()

        # Open the Output Calibration File
        k = freqfile.rfind('/')
        if not os.path.exists(DATA_PATH + str(options.board_ip) + '/CH-' + str(options.channel).zfill(2)):
            os.makedirs(DATA_PATH + str(options.board_ip) + '/CH-' + str(options.channel).zfill(2))
            os.makedirs(DATA_PATH + str(options.board_ip) + '/CH-' + str(options.channel).zfill(2) + '/Correzioni')
        out_name = DATA_PATH + str(options.board_ip) + '/CH-' + str(options.channel).zfill(
            2) + '/Correzioni/' + datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()),
                                                             "%Y-%m-%d_%H%M%S_") + 'CH-' + str(options.channel).zfill(
            2) + '_CAL_' + freqfile[k + 1:]
        out_file = open(out_name, 'w')
        records = len(freqs)

    else:
        records = 1

    start_time = time.time()
    record = 0
    next_freq = 1

    while (record < records):

        if next_freq == 1:
            # if options.verbose:
            #    print "\n",record,"\t",int(float(freqs[record])),"\t",
            # else:
            #    sys.stdout.write("\rCalibration # %d/%d" %(record+1,len(freqs)))
            #    sys.stdout.flush()
            if not options.no_sig_gen:
                cmd = 'RF ' + str(freqs[record]) + 'HZ'
                sig_gen.set_rf(freqs[record])
                freqset = int(float(sig_gen.read_rf()[2:]))
                corr_factor = cpl_att(cpl_curve, freqset)
                set_level = -2  # corr_factor
                cmd = 'LEVEL ' + str(set_level) + ' dBm'
                new_level = set_level
                sig_gen.set_level(set_level)
                path = DATA_PATH + 'CH-' + str(options.channel).zfill(2) + '/' + datetime.datetime.strftime(
                    datetime.datetime.utcfromtimestamp(time.time()), "%Y-%m-%d_%H%M%S_") + str(freqset) + "/"
                sys.stdout.write("\r[%d/%d]  Freq: %d Hz, calibrating levels..." % (
                record + 1, records, int(float(path.split('_')[-1][:-1]))))
                time.sleep(0.5)
            else:
                # path = DATA_PATH+'CH-'+str(options.channel).zfill(2)+'\\'+datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()),"%Y-%m-%d_%H%M%S\\")
                path = DATA_PATH + str(options.board_ip) + '/CH-' + str(options.channel).zfill(2) + '/'
                print "Data will be saved in: ", path
        else:
            if not options.no_sig_gen:
                cmd = 'LEVEL ' + "%3.1f" % new_level + ' dBm'
                sig_gen.set_level(new_level)

        # Measure with the power sensor
        if not options.no_sig_gen:
            pow_meter.write('FREQ ' + str(freqset) + ' HZ')
            time.sleep(0.1)

            try:
                power = float(pow_meter.query('MEASURE?')) - corr_factor
            except:
                power = -100

            diff = power - TARGET_LEVEL  # - corr_factor
            if options.verbose:
                print("\nFreq: %d\tTarget: %3.1f\tPow: %3.2f\tDiff: %3.2f\tSet: %3.1f" % (
                freqset, TARGET_LEVEL, power, diff, new_level))
            else:
                sys.stdout.write("\r[%d/%d]  Freq: %d Hz, calibrating levels..." % (
                record + 1, len(freqs), int(float(path.split('_')[-1][:-1]))))

            if abs(diff) < 0.08:
                next_freq = 1
                record += 1
                amps = float(supply.query('IOUT?')[4:])
                out_file.write('%d   %9d   %9d   %3.1f   %3.2f   %3.2f\n' % (
                record, int(float(freqs[record - 1])), freqset, new_level, power, amps))

                # Possiamo fare le misure
                if not os.path.exists(path):
                    os.makedirs(path)

                # options.output_folder = path              # verificare

                num = int(options.acq_num)
                done = 0
                UDP_PORT = 0x1234 + int(options.board_ip.split(".")[-1])
                sdp = sdp_med(UDP_PORT)
                while (done != num or num == 0):
                    snap = sdp.reassemble()
                    channel_id_list = snap[4:4 + int(snap[3])]
                    channel_list = snap[4 + int(snap[3]):]
                    # channel_id_list, channel_list = sdp.reassemble()

                    done += 1
                    if not options.no_sig_gen:
                        sys.stdout.write("\r[%d/%d]  Freq: %d Hz, Acq # %d/%d                     " % (
                        record, len(freqs), int(float(path.split('_')[-1][:-1])), done, num))
                    else:
                        sys.stdout.write("\rAcq # %d/%d" % (done, num))
                    sys.stdout.flush()

                    m = 0
                    for n in range(len(channel_id_list)):
                        if channel_id_list[n] == "1":
                            last_filename = save_raw(path, channel_list[m], n, done)
                            m += 1
                        # plot_list[n].calc(np.frombuffer(channel_list[n], dtype=np.int8))

                print("")
                del sdp
            else:
                next_freq = 0
                new_level = new_level - diff
                if new_level > SIG_GEN_MAX_LEVEL:  # max allowed by amplifier ZHL-2-3
                    # new_level = 13
                    avanti = 0
                    while avanti == 0:

                        if options.verbose:
                            print(
                                        "\n ***    Freq: %d Hz Target: %3.1f dBm, Pow: %3.1f dBm, CF: %3.2f dB, Diff: %3.2f dB, Set: %3.1f dBm (max allowed %3.1f dBm)" % (
                                freqset, TARGET_LEVEL, power, corr_factor, diff, new_level, SIG_GEN_MAX_LEVEL))

                        n = 5
                        while n > 0:
                            print(
                                        "\r[%d/%d]  Freq: %d Hz, Warning: please change the filter. Measurement retry in %2.1f seconds..." % (
                                record + 1, len(freqs), int(float(path.split('_')[-1][:-1])), n)),
                            time.sleep(0.1)
                            n = n - 0.1

                        sys.stdout.write(
                            "\r[%d/%d]  Freq: %d Hz, calibrating levels...                                                 " % (
                            record + 1, len(freqs), int(float(path.split('_')[-1][:-1]))))
                        # try:
                        # y=input("\n  -    Warning: please change the filter and then press ENTER to retry...")
                        # except SyntaxError:
                        # y = None
                        try:
                            power = float(pow_meter.query('MEASURE?')) - corr_factor
                        except:
                            time.sleep(0.1)
                        diff = power - TARGET_LEVEL
                        # diff = power - set_level
                        new_level = set_level - diff
                        if new_level <= SIG_GEN_MAX_LEVEL:
                            avanti = 1

        else:
            # Possiamo fare le misure
            if not os.path.exists(path):
                os.makedirs(path)

            num = int(options.acq_num)
            UDP_PORT = 0x1234 + int(options.board_ip.split(".")[-1])
            done = 0
            sdp = sdp_med(UDP_PORT)
            while (done != num or num == 0):
                snap = sdp.reassemble()
                channel_id_list = snap[4:4 + int(snap[3])]
                channel_list = snap[4 + int(snap[3]):]
                # channel_id_list, channel_list = sdp.reassemble()

                done += 1
                sys.stdout.write("\rAcq # %d/%d" % (done, num))
                sys.stdout.flush()
                m = 0
                # print  len(channel_id_list)
                for n in range(len(channel_id_list)):
                    if channel_id_list[n] == "1" and int(options.channel) == 32:
                        last_filename = save_raw(path, channel_list[n], n, done)
                        m += 1
                    elif channel_id_list[n] == "1" and n == int(options.channel):
                        last_filename = save_raw(path, channel_list[n], n, done)
                        m += 1

            del sdp
            record += 1

    if not options.no_sig_gen:
        # Closing file
        out_file.close()
        # Closing device
        pow_meter.close()
        del sig_gen
        supply.close()
    # del sdp
    print("\n\nMeasurements Completed in %d seconds." % (time.time() - start_time))

    if options.plotta and int(options.channel) < 32:
        # print "\nPlotting "+last_filename[:-10]+str(options.channel).zfill(2)+last_filename[-8:]
        # os.system("python tpm_reader.py -f "+last_filename[:-10]+str(options.channel).zfill(2)+last_filename[-8:])

        gs = gridspec.GridSpec(2, 1, height_ratios=[6, 1])
        fig = plt.figure(figsize=(9, 6), facecolor='w')
        # plt.ion()
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        ch = path.split("/")[-2]
        board = path.split("/")[-3]
        tpm_str = "   TPM Input: " + MAP[int(ch[-2:])][0] + "  Pol-" + MAP[int(ch[-2:])][1]
        title = "Board: #" + board.split(".")[-1] + "  ADU Channel #" + ch[-2:] + ",  " + tpm_str
        l = sorted(glob.glob(path + "*bin"))
        dati = readfile(l[0])
        spettri = np.zeros(len(calcSpectra(dati)))
        print ""
        for f in l:
            dati = readfile(f)
            sys.stdout.write("\rProcessing file: " + f)
            sys.stdout.flush()
            spettri[:] += calcSpectra(dati)
        spettri /= len(l)
        spettri += 10
        ax1.cla()
        plotta_spettro(ax1, spettri, title)
        if not os.path.isdir("images"):
            os.makedirs("images")
        ax2.cla()
        ax2.plot(range(100), color='w')
        ax2.set_axis_off()

        if options.scope:
            ax1.plot(np.zeros(400) + 6, color='r', linestyle="--")
            ax1.plot(np.zeros(400) - 6, color='r', linestyle="--")
            ax1.annotate("Gain High Limit", xy=(200, 7), xytext=(202, 7), color='r', fontsize=10)
            ax1.annotate("Gain Low Limit", xy=(200, -10), xytext=(202, -9.5), color='r', fontsize=10)

            hds = mark_armonics(ax1, spettri, 10)

            wo = worst_other(spettri, hds, (50, 350))
            if hds[0] > 17800:
                ct = worst_other(spettri, hds, (105.8, 106))
            else:
                ct = worst_other(spettri, hds, (111.5, 111.7))

            tone_freq = "%f" % (hds[0] * 400. / 65536)
            tone_freq = tone_freq[:7] + "." + tone_freq[7:]

            ax1.annotate("Total Gain: " + "%3.1f" % (60 + spettri[hds[0]]) + " dB", (151, -19), fontsize=12)

            ax2.annotate("Foundamental Tone: " + "%3.1f" % (spettri[hds[0]]) + " dBm", (1, 82), fontsize=12)
            ax2.annotate("Second Harmonic: " + "%3.1f" % (spettri[hds[1]]) + " dBm", (1, 42), fontsize=12)
            ax2.annotate("Third Harmonic: " + "%3.1f" % (spettri[hds[2]]) + " dBm", (1, 2), fontsize=12)

            ax2.annotate("Tone Frequency: " + tone_freq + " Hz", (40, 82), fontsize=12)

            ax2.annotate("Cross Talk: " + "%3.1f" % (spettri[hds[0]] - ct[0]) + " dBC @ " + "%6.3f" % (ct[1]) + " MHz",
                         (40, 2), fontsize=12)
            ax1.plot(ct[1] - 1, ct[0] - 1, color='y', marker="o")
            ax1.annotate("CT", xy=(ct[1] - 10, ct[0] + 2), xytext=(ct[1] - 10, ct[0] + 2), fontsize=9)

            ax2.annotate("Worst Other: " + "%3.1f" % (wo[0]) + " dBm  @ " + "%6.3f" % (wo[1]) + " MHz", (40, 42),
                         fontsize=12)
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

        sys.stdout.write("\rDirectory processed: " + path + "                       \n")
        sys.stdout.flush()
