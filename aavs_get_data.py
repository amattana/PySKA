#import visa
import os,sys
#import easygui
import time,datetime
from optparse import OptionParser
import numpy as np
import socket
sys.path.append("../rf_jig")
sys.path.append("../board")

from netproto.sdp_medicina import sdp_medicina as sdp_med
from struct import *

from tpm_utils import *
#from qt_rf_jig_utils import *
from SMY02 import RS_SMY02

TARGET_LEVEL = 10.4 # NO ADA
#TARGET_LEVEL = -9.4 # CON ADA
POW_METER_TIMEOUT = 2000
SIG_GEN_MAX_LEVEL = 13

SW_PATH = "D:\\SKA-TPM\\"
DATA_PATH = "/home/oper/data/"

GEN_ADDR = 25
POWMETER_ADDR = 14
POWSENSOR_ADDR = 0
SPECTAN_ADDR = 18

HPIB_DB_FILE = "HPIB_DB.txt"
FILE_CPL     = "CPL_CURVE.txt"

THIS_UDP_IP = "10.0.10.1"
FPGA_UDP_IP = "10.0.10.2"
UDP_PORT = 0x1236


def eq_retta(x1,y1,x2,y2):
    m=float(y2-y1)/(x2-x1)
    q=y1-(m*x1)
    def retta(x):
        return m*x + q
    return retta

def cpl_att(cpl_curve,freq_set):
    #print freq_set
    for i in range(len(cpl_curve)):
        if cpl_curve[i][0] > freqset:
            break
    if i > 0:
        r = eq_retta(cpl_curve[i][0],cpl_curve[i][1],cpl_curve[i-1][0],cpl_curve[i-1][1])
    else:
        r = eq_retta(cpl_curve[0][0],cpl_curve[0][1],cpl_curve[1][0],cpl_curve[1][1])
    return r(freqset)

def read_cpl_curve(file_cpl):
    cpl_curve = []
    f_cpl = open(file_cpl,'r')
    cpl_list = f_cpl.readlines()
    for i in range(len(cpl_list)):
        #print cpl_list[i][:-1].split()
        cpl_curve += [[int(cpl_list[i].split()[0]),float(cpl_list[i].split()[2])]]
        #print cpl_curve[i]
        #cpl_curve[i][0] = int(cpl_curve[i][0])
        #cpl_curve[i][0] = float(cpl_curve[i][0])
    f_cpl.close()
    return cpl_curve

def ByteToHex( byteStr ):
    #"""
    #Convert a byte string to it's hex string representation e.g. for output.
    #"""
    return ''.join( [ "%02X " % ord( x ) for x in byteStr ] ).strip()


def fft(input):
   window = np.blackman(len(input))      # changed from hanning in blackman
   output = np.fft.rfft(input*window)
   N = len(output)
   acf = 2  #amplitude correction factor
   output = abs((acf*output)/N)
   output = 20*np.log10(output/128.0)
   return output
   
def modulo(input):
   output = np.zeros(len(input)/2, dtype=np.float)
   re = 0.0
   im = 0.0
   for n in range(len(input)):
      if n % 2 == 0:
         re = input[n]
      else:
         im = input[n]
      ##if n % 4 == 1:
         p = (re**2 + im**2)**0.5
         print n
         print re
         print im
         print p
         print 
         output[n/2] = p
   return output
      
def check_pattern(input):
   seed = input[0]
   for n in range(len(input)):
      recv = input[n] + 128
      if n >= 0 and n <= 11:
         exp = (seed + 128 + n%4) & 0xFF
      else:
         exp = (seed + 128 + (n-12))  & 0xFF
      if recv != exp:
         print "error at index " + str(n)
         print "expected " + str(exp)
         print "received " + str(recv)
         xx = pylab.waitforbuttonpress(timeout=0.1)
         exit()
   print "test pattern is good!"

def is_first(channel_id,channel_disable):
   ret = 0
   #print "Partiamo: ",hex(channel_id),hex(channel_disable)
   disable = channel_disable
   #print "disable=",hex(disable)
   for n in range(16):
     # print "if disable=",hex(disable) ,"& 0x1 == 0:" ,hex(disable & 0x1)
      if disable & 0x1 == 0:
        # print "if channel_id == n", hex(channel_id), n
         if channel_id == n:
            ret = 1
         break
      disable = disable >> 1
      #print "disable = disable >> 1", hex(disable)
   #print "RETURN: ", ret
   return ret

def is_last(channel_id,channel_disable):
   ret = 0
   disable = channel_disable
   for n in reversed(range(16)):
      if disable & 0x8000 == 0:
         if channel_id == n:
            ret = 1
         break
      disable = disable << 1
   return ret
   
def set_channel(channel_ok,channel_id):
   mask = 1 << channel_id
   channel_ok = channel_ok | mask;
   return channel_ok
      
      
def save_raw(path,data,chan,seq):
    raw_filename = path + "input_" + str(chan).zfill(2) + "_" + str(seq-1).zfill(3) + ".bin"
    raw_file = open(raw_filename, "wb")
    raw_file.write(data)
    raw_file.close()
    return raw_filename


parser = OptionParser()
parser.add_option("-i", "--channel", 
                  dest="channel", 
                  default = 0,
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
                  default = 100,
                  help="Number of acquisition")
parser.add_option("-b", "--board_ip",
                  dest="board_ip", 
                  default = "10.0.10.2",
                  help="Board ip, def: 10.0.10.2")
parser.add_option("--sig_gen", 
                  action="store_true",
                  dest="sig_gen", 
                  default = False,
                  help="Drive the signal generator (output folder will append the frequency)")
parser.add_option("--cp", 
                  action="store_true",
                  dest="cpl_att", 
                  default = True,
                  help="if the power is read from a coupler take into account of its attenuation")
(options, args) = parser.parse_args()


#if options.cpl_att:
#    #print "CPL Correction Factor Enabled"
#    cpl_curve = read_cpl_curve(FILE_CPL)
#    #print cpl_curve

if options.sig_gen:
    # Find GPIB plugged devices
    rm = visa.ResourceManager()
    rm_list = rm.list_resources()
    pow_meter = rm.open_resource(u'USB0::0x0957::0x2D18::MY53040009::INSTR')
    pow_meter.timeout = POW_METER_TIMEOUT
    #sig_gen = rm.open_resource(u'GPIB0::25::INSTR')
    sig_gen = RS_SMY02(iec=25)
    supply = rm.open_resource(u'GPIB0::4::INSTR')

    # Read the Input Frequencies File
    print("\nSelect a Frequencies file...")
    freqfile = easygui.fileopenbox(msg='Please select the frequencies file',
          default=SW_PATH+'Freqs\*.txt')
    print("Opening file: %s"%(freqfile))
    freq_file = open(freqfile,'r')
    freqs = freq_file.readlines()
    print "Found "+str(len(freqs))+" frequencies!\n"
    freq_file.close()

    # Open the Output Calibration File
    k = freqfile.rfind('\\')
    if not os.path.exists(DATA_PATH+'CH-'+str(options.channel).zfill(2)):
        os.makedirs(DATA_PATH+'CH-'+str(options.channel).zfill(2))
        os.makedirs(DATA_PATH+'CH-'+str(options.channel).zfill(2)+'\\Correzioni')
    out_name = DATA_PATH+'CH-'+str(options.channel).zfill(2)+'\\Correzioni\\'+datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()),"%Y-%m-%d_%H%M%S_")+'CH-'+str(options.channel).zfill(2)+'_CAL_'+freqfile[k+1:]
    out_file = open(out_name,'w')
    records = len(freqs)

else:
    records = 1



start_time = time.time()
record=0
next_freq = 1
    
while (record < records):

    if next_freq == 1:
        #if options.verbose:
        #    print "\n",record,"\t",int(float(freqs[record])),"\t",
        #else:
        #    sys.stdout.write("\rCalibration # %d/%d" %(record+1,len(freqs)))
        #    sys.stdout.flush()
        if options.sig_gen:
            cmd = 'RF '+ str(freqs[record]) + 'HZ'
            sig_gen.set_rf(freqs[record])
            freqset = int(float(sig_gen.read_rf()[2:]))
            corr_factor=cpl_att(cpl_curve,freqset)    
            set_level = -2 #corr_factor
            cmd = 'LEVEL ' + str(set_level) + ' dBm'
            new_level = set_level
            sig_gen.set_level(set_level)
            path = DATA_PATH+'CH-'+str(options.channel).zfill(2)+'\\'+datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()),"%Y-%m-%d_%H%M%S_")+str(freqset)+"\\"
            sys.stdout.write("\r[%d/%d]  Freq: %d Hz, calibrating levels..." %(record+1,records,int(float(path.split('_')[-1][:-1]))))
            time.sleep(0.5)
        else:
            #path = DATA_PATH+'CH-'+str(options.channel).zfill(2)+'\\'+datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(time.time()),"%Y-%m-%d_%H%M%S\\")
            path = DATA_PATH+options.board_ip+'/CH-'+str(options.channel).zfill(2)+'/'
            print "Data will be saved in: ",path
    else:
        if options.sig_gen:
            cmd = 'LEVEL ' + "%3.1f"%new_level + ' dBm'
            sig_gen.set_level(new_level)



    # Measure with the power sensor
    if options.sig_gen:
        pow_meter.write('FREQ '+str(freqset)+' HZ')
        time.sleep(0.1)
        
        try:
            power = float(pow_meter.query('MEASURE?')) - corr_factor
        except:
            power = -100
    
        diff = power - TARGET_LEVEL #- corr_factor
        if options.verbose:
            print("\nFreq: %d\tTarget: %3.1f\tPow: %3.2f\tDiff: %3.2f\tSet: %3.1f"%(freqset,TARGET_LEVEL,power,diff,new_level))
        else:
            sys.stdout.write("\r[%d/%d]  Freq: %d Hz, calibrating levels..." %(record+1,len(freqs),int(float(path.split('_')[-1][:-1]))))

        if abs(diff) < 0.08 :
            next_freq = 1
            record += 1
            amps = float(supply.query('IOUT?')[4:])
            out_file.write('%d   %9d   %9d   %3.1f   %3.2f   %3.2f\n'%(record,int(float(freqs[record-1])),freqset,new_level,power,amps))
        
            # Possiamo fare le misure
            if not os.path.exists(path):
                os.makedirs(path)

            # options.output_folder = path              # verificare

            num = int(options.acq_num)
            done = 0
            UDP_PORT = 0x1234 + int(options.board_ip.split(".")[-1])
            sdp = sdp_med(UDP_PORT)
            while(done != num or num == 0):
                snap =  sdp.reassemble()
                channel_id_list = snap[4:4+int(snap[3])]
                channel_list = snap[4+int(snap[3]):]
                #channel_id_list, channel_list = sdp.reassemble()

                done += 1
                if not options.no_sig_gen:
                    sys.stdout.write("\r[%d/%d]  Freq: %d Hz, Acq # %d/%d                     " %(record,len(freqs),int(float(path.split('_')[-1][:-1])),done,num))
                else:
                    sys.stdout.write("\rAcq # %d/%d" %(done,num))
                sys.stdout.flush()

                m = 0
                for n in range(len(channel_id_list)):
                    if channel_id_list[n] == "1":
                        last_filename=save_raw(path, channel_list[m],n,done)
                        m += 1
                        #plot_list[n].calc(np.frombuffer(channel_list[n], dtype=np.int8))

            print("")
            del sdp
        else: 
            next_freq = 0
            new_level = new_level - diff
            if  new_level > SIG_GEN_MAX_LEVEL: # max allowed by amplifier ZHL-2-3
                #new_level = 13
                avanti = 0
                while avanti==0:
                
                    if options.verbose:
                        print("\n ***    Freq: %d Hz Target: %3.1f dBm, Pow: %3.1f dBm, CF: %3.2f dB, Diff: %3.2f dB, Set: %3.1f dBm (max allowed %3.1f dBm)"%(freqset,TARGET_LEVEL,power,corr_factor,diff,new_level,SIG_GEN_MAX_LEVEL))

                    n=5
                    while n>0:
                        print("\r[%d/%d]  Freq: %d Hz, Warning: please change the filter. Measurement retry in %2.1f seconds..."%(record+1,len(freqs),int(float(path.split('_')[-1][:-1])),n)),
                        time.sleep(0.1)
                        n = n -0.1  
                
                    sys.stdout.write("\r[%d/%d]  Freq: %d Hz, calibrating levels...                                                " %(record+1,len(freqs),int(float(path.split('_')[-1][:-1]))))
                    #try:
                        #y=input("\n  -    Warning: please change the filter and then press ENTER to retry...")
                    #except SyntaxError:
                        #y = None
                    try:
                        power = float(pow_meter.query('MEASURE?')) - corr_factor
                    except:
                        time.sleep(0.1)
                    diff = power - TARGET_LEVEL
                    #diff = power - set_level
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
        while(done != num or num == 0):
            snap =  sdp.reassemble()
            channel_id_list = snap[4:4+int(snap[3])]
            channel_list = snap[4+int(snap[3]):]
            #channel_id_list, channel_list = sdp.reassemble()

            done += 1
            sys.stdout.write("\rAcq # %d/%d" %(done,num))
            sys.stdout.flush()
            m = 0
            #print  len(channel_id_list)
            for n in range(len(channel_id_list)):
                if channel_id_list[n] == "1" and int(options.channel)==32:
                    last_filename=save_raw(path, channel_list[n],n,done)
                    m += 1
                elif channel_id_list[n] == "1" and n==int(options.channel):
                    last_filename=save_raw(path, channel_list[n],n,done)
                    m += 1

        del sdp
        record += 1

    
    
if options.sig_gen:
    # Closing file
    out_file.close()
    # Closing device
    pow_meter.close()
    del sig_gen
    supply.close()
#del sdp
print("\n\nMeasurements Completed in %d seconds." % (time.time() - start_time))

if options.plotta and int(options.channel)<32:
    print "\nPlotting "+last_filename[:-10]+str(options.channel).zfill(2)+last_filename[-8:]
    os.system("tpm_reader.py -f "+last_filename[:-10]+str(options.channel).zfill(2)+last_filename[-8:])

