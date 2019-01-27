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


def processQPIRI(res):
    print ("Grid rating voltage : " + res[1:6] + " V")
    print ("Grid rating current : " + res[7:11] + " A")
    print ("AC output rating voltage : " + res[12:17] + " V")
    print ("AC output rating frequency : " + res[18:22] + " Hz")
    print ("AC output rating current : " + res[23:27] + " A")
    print ("AC output rating apparent power : " + res[28:32] + " VA")
    print ("AC output rating active power : " + res[33:37] + " W")
    print ("Battery rating voltage : " + res[38:42] + " V")
    print ("Battery re-charge voltage : " + res[43:47] + "V ")
    print ("Battery under voltage : " + res[48:52] + " V")
    print ("Battery bulk voltage : " + res[53:57] + " V")
    print ("Battery float voltage : " + res[58:62] + " V")
    if res[63:64] == "0":
            print ("Battery type : AGM")
    elif res[63:64] == "1":
            print ("Battery type : Flooded")
    elif res[63:64] == "2":
            print ("Battery type : User")
    print ("Current max AC charging current : " + res[65:67] + " A")
    print ("Current max charging current : " + res[68:71] + " A")
    if res[72:73] == "0":
        print ("Input voltage range : Appliance (From 90V to 280V AC)")
    elif res[72:73] == "1":
        print ("Input voltage range : UPS (From 170V to 280V AC)")

    if res[74:75] == "0":
        print ("Output source priority : Utility first")
    elif res[74:75] == "1":
        print ("Output source priority : Solar first")
    elif res[74:75] == "2":
        print ("Output source priority : SBU first")
    
    if res[76:77] == "0":
        print ("Charger source priority : Utility first")
    elif res[76:77] == "1":
        print ("Charger source priority : Solar first")
    elif res[76:77] == "2":
        print ("Charger source priority : Solar + Utility")
    elif res[76:77] == "3":
        print ("Charger source priority : Only solar charging permitted")
    
    print ("Battery re-discharge voltage : " + res[87:91] + " V")
    return

def processQPIGS(res):
    print ("Grid voltage : " + res[1:6] + " V")
    print ("Grid frequency : " + res[7:11] + " Hz")
    print('-' * 40)
    print ("AC output voltage : " + res[12:17] + " V")
    print ("AC output frequency : " + res[18:22] + " Hz")
    print ("AC output apparent power : ", int(res[23:27]), "VA")
    print ("AC output active power : ", int(res[28:32]), "W")
    print ("AC output load percent : ", int(res[33:36]), "%")
    print('-' * 40)
    print ("BUS voltage : " + res[37:40] + " V")
    print ("Battery voltage : " + res[41:46] + " V")
    print ("Battery charging current : " + res[47:50] + " A")
    print ("Battery capacity : " + res[51:54] + " %")
    print ("Battery voltage from SCC 1 : " + res[71:76] + " V")
    print ("Battery discharge current : " + res[77:82] + " A")
    print('-' * 40)
    print ("Inverter heat sink temperature : ", int(res[55:59]),"C")
    print('-' * 40)
    print ("PV Input current 1 : ", float(res[60:64]), "A")
    print ("PV Input voltage 1 : ", float(res[65:70]), "V")
    print ("PV Charging power 1 : ", int(res[98:103]), "W")
    print('-' * 40)
    print ("Device status : " + res[83:90])
    return


def processQPIGS2(res):
    print ("PV Input current 2 : " + res[1:5] + " A")
    print ("PV Input voltage 2 : " + res[6:11] + " V")
    print ("Battery voltage from SCC 2 : " + res[12:17] + " V")
    print ("PV Charging power 2: " + res[18:23] + " W")
    print ("Device status: " + res[24:32])
    print ("AC charging current : " + res[33:37] + " A")
    print ("AC charging power : " + res[38:42] + " W")
    print('-' * 40)
    return

def processQPIWS(res):
    print("Over charge current : " + res[1])
    print("Over temperature : " + res[2])
    print("Battery voltage under : " + res[3])
    print("Battery voltage high : " + res[4])
    print("PV high loss : " + res[5])
    print("Battery temperature too low : " + res[6])
    print("Battery temperature too high " + res[7])
    print("PV low loss : " + res[20])
    print("PV high derating : " + res[21])
    print("Temperature high derating : " + res[22])
    print("Battery temperature low alarm : " + res[23])
    return

#print(sys.argv[0])

ts = int(time.time())
print (ts)

#print ("flushing buffer...")
buffer=getResult(5)

#get device protocol version
#deviceProtocol=getStrData('QPI',1,5)
#print (deviceProtocol)

#get device serial Number
#deviceSerialNumber=getStrData('QID',1,14)
#print (deviceSerialNumber)

#get CPU firmware version
#inverterCPUFirmware=getStrData('QVFW',1,15)
#print (inverterCPUFirmware)

#get SCC1 firmware version
#SCC1Firmware=getStrData('QVFW2',1,16)
#print (SCC1Firmware)

#get device rating information
deviceRatingInformation=getStrData('QPIRI',0,98)
if len(deviceRatingInformation) >= 98 :
    print('=' * 40)
    print("QIPRI", len(deviceRatingInformation),deviceRatingInformation)
    print('=' * 40)
    processQPIRI(deviceRatingInformation)
else:
    sys.exit(1)
#get device Flag status


#get device general status
deviceGeneralStatus=getStrData('QPIGS',0,107)
if len(deviceGeneralStatus) >= 107:
    print('=' * 40)
    print ("QPIGS",len(deviceGeneralStatus),deviceGeneralStatus)
    print('=' * 40)
    processQPIGS(deviceGeneralStatus)
else:
    sys.exit(1)

#get device warning status
deviceWarningStatus=getStrData('QPIWS',0,30)
if len(deviceWarningStatus) >= 30:
    print('=' * 40)
    print ("QPIWS",len(deviceWarningStatus),deviceWarningStatus)
    print('=' * 40)
    #processQPIWS(deviceWarningStatus)
else:
    sys.exit(1)
#get device general status
#deviceGeneralStatus2=getStrData('QPIGS2',0,68)
#processQPIGS2(deviceGeneralStatus2)
now = datetime.datetime.now()
print ("Current date and time : ")
print (now.strftime("%Y-%m-%d %H:%M:%S"))
