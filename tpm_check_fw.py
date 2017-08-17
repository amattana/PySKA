#!/usr/bin/python2.7

import os,sys
from tpm_utils import *
sys.path.append("../board")
sys.path.append("../rf_jig")
sys.path.append("../config")
sys.path.append("../repo_utils")
from bsp.tpm import *
import subprocess
DEVNULL = open(os.devnull,'w')
from ip_scan import *

def tpm_obj(loc_ip):
    tpm = {}
    tpm['TPM'] = TPM(ip=loc_ip, port=10000, timeout=1)
    tpm['IP']  = loc_ip
    return tpm

#TPMs=['10.0.10.2', '10.0.10.3', '10.0.10.4', '10.0.10.5', '10.0.10.6', '10.0.10.25']
TPMs=ip_scan()

tpms = []
for i in range(len(TPMs)):
    tpms += [tpm_obj(TPMs[i])]
print

print "  TPM IP\tCPLD FW Ver\tFPGA FW Ver\t  REF\t ADCs\t Temp"
print "---------------------------------------------------------------------"
for i in range(len(TPMs)):
    if subprocess.call(['python','ip_check.py','-i',tpms[i]['IP']],stdout=DEVNULL)==0:
        msg = tpms[i]['IP']+"\t"+getCpldFwVersion(tpms[i]['TPM'])+"\t "+getFpgaFwVersion(tpms[i]['TPM']) 
        if getPLLStatus(tpms[i]['TPM'])==0xe7:
            msg += "\tlck_ext"
        elif getPLLStatus(tpms[i]['TPM'])==0xf2:
            msg += "\tlck_int"
        else:
            msg += "\tunlck"
        if getADCStatus(tpms[i]['TPM'])==0:
            msg += "\tadc_off"
        else:
            msg += "\tadc_on"
        msg += "\t %3.1f"%(getTpmTemp(tpms[i]['TPM']))
        print msg


print
print


