#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import datetime 
import usb.core, usb.util, usb.control
import crc16
import time

vendorId = 0x0665
productId = 0x5161
interface = 0


dev = usb.core.find(idVendor=vendorId, idProduct=productId)
if dev is None:
        raise ValueError('Device not found')

if dev.is_kernel_driver_active(interface):
        dev.detach_kernel_driver(interface)
        dev.set_interface_altsetting(0,0)


def getCommand(cmd):
    cmd = cmd.encode('utf-8')
    crc = crc16.crc16xmodem(cmd).to_bytes(2,'big')
    cmd = cmd+crc
    cmd = cmd+b'\r'
    while len(cmd)<8:
        cmd = cmd+b'\0'
    return cmd

def sendCommand(cmd):
    dev.ctrl_transfer(0x21, 0x9, 0x200, 0, cmd)

def getResult(timeout=100):
    res=""
    i=0
    while '\r' not in res and i<150:
        try:
            res+="".join([chr(i) for i in dev.read(0x81, 8, timeout) if i!=0x00])
        except usb.core.USBError as e:
            if e.errno == 110:
                pass
            else:
                raise
        i+=1
    return res

def getStrData(cmd,start,end):
    sendCommand(getCommand(cmd))
    res = getResult().encode("utf-8")
    #print (cmd, len(res))
    return res[start:end].decode("utf-8") if len(res)>end else "Nan"


def RRDUpdateData(ts,res):
    pu=int(res[28:32])
    #print ("AC output load percent : ", int(res[33:36]), "%")
    #print ("Battery charging current : " + res[47:50] + " A")
    #print ("Battery capacity : " + res[51:54] + " %")
    batv=float(res[71:76])
    bati=float(res[77:82])
    ps=int(res[98:103])
    output=str(ts)+":"+str(pu)+":"+str(ps)+":"+str(bati)+":"+str(batv)
    print (output)
    return


ts = int(time.time())

buffer=getResult(5)

#get device general status
deviceGeneralStatus=getStrData('QPIGS',0,107)
if len(deviceGeneralStatus) >= 107:
    RRDUpdateData(ts,deviceGeneralStatus)
else:
    sys.exit(1)
