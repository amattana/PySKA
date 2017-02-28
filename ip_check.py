import socket,sys
import struct
import binascii

sys.path.append("../")
sys.path.append("../../")
sys.path.append("../board")
sys.path.append("../config")
sys.path.append("../repo_utils")
sys.path.append("../board/pyska")
import config.manager as config_man
from bsp.tpm import *
from optparse import OptionParser

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--ip", 
                      dest="ip", 
                      default = "10.0.10.2",
                      help="FPGA IP")
                      
    (options, args) = parser.parse_args()

    config = config_man.get_config_from_file(config_file="../config/config.txt", design="tpm_test", display=False,check=True, sim="")
    tpm_inst = TPM(ip=options.ip, port=config['UDP_PORT'], timeout=config['UDP_TIMEOUT'])
    code=-1
    try:
        prova=tpm_inst[0]
        #print "ONLINE"
        code=0
    except:
        #print "OFFLINE -2"
        code=-2
        
    exit(code)
