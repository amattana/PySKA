import multiprocessing
import subprocess
import os, time, sys
import platform
import re


def pinger( job_q, results_q ):
    DEVNULL = open(os.devnull,'w')
    while True:
        FPGA_IP = job_q.get()
        if FPGA_IP==None:
            break
        try:
            if subprocess.call(['python','ip_check.py','-i',FPGA_IP],stdout=DEVNULL)==0:#)
                results_q.put(FPGA_IP)
        except:
            pass

def get_lista_serial():
    a=open("itpm_mac_addr.txt")
    listamac=a.readlines()
    a.close()
    if re.sub('[ \n]','',listamac[-1])=="":
        lines=listamac[:-1]
        listamac=lines
    #print listamac,len(listamac)
    return listamac

def get_serial_from_mac(listamac, addr):
    sn=""
    tpmnum=""
    i=0
    trovato=False
    while i<(len(listamac)) and trovato==False:
        #print listamac[i].split()[0], addr
        if addr.replace('-',':')==listamac[i].split()[0].replace('-',':'):
            trovato=True
            sn=re.sub('[ \n]','',listamac[i].split()[1])
            try:
                tpmnum=re.sub('[ \n]','',listamac[i].split()[2])
            except:
                tpmnum=''
                pass
        i=i+1
    return sn,tpmnum

def ip_scan():
    pool_size = 32
    #print "START"

    jobs = multiprocessing.Queue()
    results = multiprocessing.Queue()

    print "\nScanning network 10.0.10.0/24, please wait..."
    pool = [ multiprocessing.Process(target=pinger, args=(jobs,results))
             for i in range(pool_size) ]

    for p in pool:
        p.start()

    for i in range(1,pool_size+1):
        jobs.put('10.0.10.{0}'.format(i))
        #time.sleep(1)

    for p in pool:
        jobs.put(None)

    for p in pool:
        p.join()

    print
    lista_ip = []
    while not results.empty():
        lista_ip += [results.get()] 
    if lista_ip==[]:
        print "No iTPM boards found!"
    else:
        listamac=get_lista_serial()
        print "    IP     \t     MAC addr\t\tSerial Number\t   TPM#"
        print "------------------------------------------------------------------"
        for ip in lista_ip:
            if platform.system()=="Linux":
                p = subprocess.Popen(['arp', '-n',ip], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            else:
                p = subprocess.Popen(['arp', '-a',ip], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out, err = p.communicate()
            mac="n/a"
            if not platform.system()=="Linux":
                if out.split("\n")[3].split()[0]==ip:
                    mac=out.split("\n")[3].split()[1]
            else:
                if out.split("\n")[1].split()[0]==ip:
                    mac=out.split("\n")[1].split()[2]
            seriale,aavs1num = get_serial_from_mac(listamac, mac)
            print ip,"\t", mac,"\t ", seriale,"\t   ",aavs1num 
    print
    
    return lista_ip
        
if __name__ == "__main__":
    a=ip_scan()