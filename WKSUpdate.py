#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import paho.mqtt.client as mqtt
import datetime 
import usb.core, usb.util, usb.control
import crc16
import time

vendorId = 0x0665
productId = 0x5161
interface = 0
debug = False

#Kwh counter update every xx s
Consumption_Calculation=10

#init Global Energy counter
Grid_Consumption=0
Solar_Consumption=0
From_Battery_Consumption=0
To_Battery_Consumption=0
ACOut_Consumption=0

#Temp_counter
T0_Grid=0
T1_Grid=0
V0_Grid=0
V1_Grid=0
Cumulated_Grid_Ws=0
cumulated_Grid_T=0

T0_Solar=0
T1_Solar=0
V0_Solar=0
V1_Solar=0
Cumulated_Solar_Ws=0
Cumulated_Solar_T=0

T0_Battery=0
T1_Battery=0
V0_From_Battery=0
V1_From_Battery=0
V0_To_Battery=0
V1_To_Battery=0
Cumulated_From_Battery_Ws=0
Cumulated_To_Battery_Ws=0
Cumulated_Battery_T=0

T0_ACOut=0
T1_ACOut=0
V0_ACOut=0
V1_ACOut=0
Cumulated_ACOut_Ws=0
Cumulated_AcOout_T=0

print ("Starting WKS Update service")

dev = usb.core.find(idVendor=vendorId, idProduct=productId)
if dev is None:
        raise ValueError('Device not found')
else: 
    print ("WKS is connected")

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


#Send command overs USB link
#TODO : Manager Errori, Try/Excep
def sendCommand(cmd):
    dev.ctrl_transfer(0x21, 0x9, 0x200, 0, cmd)

#Read information from USB Link
#TODO: Manage Error, Try/Excep
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

#Send and receive Data using SendCommand an getResult function
#TODO: Manage Erreo code return by SendCommand and getResult
def getStrData(cmd,start,end):
    sendCommand(getCommand(cmd))
    res = getResult().encode("utf-8")
    #print (cmd, len(res))
    return res[start:end].decode("utf-8") if len(res)>end else "Nan"


#This functin process the Inverter "Get configuration" result in human readable values 
def processQPIRI(res):
    if debug:
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
        print ("Current max AC charging current : " + res[65:68] + " A")
        print ("Current max charging current : " + res[69:72] + " A")
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
        
        print ("Battery re-discharge voltage : " + res[87:92] + " V")
    return


#This function process the Inverter "Get current Status" en translate in Readable Human Values
# Also Make calculation for Kwh counter and publish data in MQTT Server

def processQPIGS(res,client):
    global Current_Day,Consumption_Calculation,Grid_Consumption,Solar_Consumption,From_Battery_Consumption,To_Battery_Consumption,ACOut_Consumption, \
            T0_Grid,T1_Grid,V0_Grid,V1_Grid,Cumulated_Grid_Ws,Cumulated_Grid_T,\
            T0_Solar,T1_Solar,V0_Solar,V1_Solar,Cumulated_Solar_Ws,Cumulated_Solar_T,\
            T0_Battery,T1_Battery,V0_Battery,V1_Battery,Cumulated_To_Battery_Ws,Cumulated_From_Battery_Ws,Cumulated_Battery_T,\
            T0_ACOut,T1_ACOut,V0_ACOut,V1_ACOut,Cumulated_ACOut_Ws,Cumulated_ACOut_T
            

    if debug:
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
        print ("Battery charging current : ", float(res[47:50])," A")
        print ("Battery capacity : ", int(res[51:54]), " %")
        print ("Battery voltage from SCC 1 : " + res[71:76] + " V")
        print ("Battery discharge current : ", float (res[77:82])," A")
        print('-' * 40)
        print ("Inverter heat sink temperature : ", int(res[55:59]),"C")
        print('-' * 40)
        print ("PV Input current 1 : ", float(res[60:64]), "A")
        print ("PV Input voltage 1 : ", float(res[65:70]), "V")
        print ("PV Charging power 1 : ", int(res[98:103]), "W")
        print('-' * 40)
        print ("Device status : " + res[83:90])

    ts = int(time.time())
    now = datetime.datetime.now()
    Today=now.strftime("%Y-%m-%d")
    if Today!=Current_Day:
        #init Global Energy counter
        Grid_Consumption=0
        Solar_Consumption=0
        From_Battery_Consumption=0
        To_Battery_Consumption=0
        ACOut_Consumption=0
        Current_Day=Today

    Grid_Voltage=float(res[1:6])
    Grid_Frequency=float(res[1:6])
    
    AC_Output_Voltage=float(res[12:17])
    AC_Output_Frequency=float(res[18:22])
    if (int(res[23:27])!=0):
        AC_Output_Current=float(int(res[23:27])/float(res[12:17]))
    else:
        AC_Output_Current=float("0.00")
    AC_Output_Active_Power=int(res[28:32])
    AC_Output_Power=int(res[23:27])

    DC_Voltage=float(res[41:46])
    DC_Current=int(res[47:50])-int(res[77:82])
    DC_Power=DC_Voltage*DC_Current

    PV_Voltage=float(res[65:70])
    PV_Current=int(res[60:64])
    PV_Power=int(res[98:103])
    Device_Status=res[83:90]

    Grid_Power=AC_Output_Active_Power-DC_Power-PV_Power

    #init value at first run
    if T0_Grid==0:
        T0_Grid=ts
        T0_Solar=ts
        T0_Battery=ts
        T0_ACOut=ts
        #Value in Watt for each input/output
        V0_Grid=Grid_Power
        V0_Solar=PV_Power
        V0_Battery=DC_Power
        V0_ACOut=AC_Output_Power

        Cumulated_Grid=0
        Cumulated_Battery=0
        Cumulated_Solar=0
        Cumulated_ACOut=0

        Cumulated_Grid_T=0
        Cumulated_Battery_T=0
        Cumulated_Solar_T=0
        Cumulated_ACOut_T=0
    else:
        T1_Grid=ts
        T1_Solar=ts
        T1_Battery=ts
        T1_ACOut=ts

        #Calculate Delta Time since last run
        DeltaT_Grid=T1_Grid-T0_Grid
        DeltaT_Solar=T1_Solar-T0_Solar
        DeltaT_Battery=T1_Battery-T0_Battery
        DeltaT_ACOut=T1_ACOut-T0_ACOut
        
        #Re init T0 for next run
        T0_Grid=T1_Grid
        T0_Solar=T1_Solar
        T0_Battery=T1_Battery
        T0_ACOut=T1_ACOut

        #Values in Watt for each input/output
        V1_Grid=Grid_Power
        V1_Solar=PV_Power
        V1_Battery=DC_Power
        V1_ACOut=AC_Output_Active_Power

        #Cumulated Time since Kwh Calcul
        Cumulated_Solar_T = Cumulated_Solar_T + DeltaT_Solar
        Cumulated_Battery_T = Cumulated_Battery_T + DeltaT_Battery
        Cumulated_ACOut_T = Cumulated_ACOut_T + DeltaT_ACOut

        if DeltaT_Grid !=0:
            Cumulated_Grid_Ws=Cumulated_Grid_Ws + ((V1_Grid + V0_Grid)/2)*DeltaT_Grid
            Cumulated_Grid_T = Cumulated_Grid_T + DeltaT_Grid
            V0_Grid=V1_Grid
            if Cumulated_Grid_T>Consumption_Calculation:
                Grid_Consumption=Grid_Consumption+(Cumulated_Grid_Ws/3600/1000)
                Cumulated_Grid_Ws=0
                Cumulated_Grid_T=0

        if DeltaT_Solar !=0:
            Cumulated_Solar_Ws=Cumulated_Solar_Ws + ((V1_Solar + V0_Solar)/2)*DeltaT_Solar
            Cumulated_Solar_T = Cumulated_Solar_T + DeltaT_Solar
            V0_Solar=V1_Solar
            if Cumulated_Solar_T>Consumption_Calculation:
                Solar_Consumption=Solar_Consumption+(Cumulated_Solar_Ws/3600/1000)
                Cumulated_Solar_Ws=0
                Cumulated_Solar_T=0


        if DeltaT_Battery !=0:
            if (V1_Battery + V0_Battery)>0:
                Cumulated_To_Battery_Ws=Cumulated_To_Battery_Ws + ((V1_Battery + V0_Battery)/2)*DeltaT_Battery
            else:
                Cumulated_From_Battery_Ws=Cumulated_From_Battery_Ws - ((V1_Battery + V0_Battery)/2)*DeltaT_Battery
            Cumulated_Battery_T = Cumulated_Battery_T + DeltaT_Battery
            V0_Battery=V1_Battery
            if Cumulated_Battery_T>Consumption_Calculation:
                To_Battery_Consumption=To_Battery_Consumption+(Cumulated_To_Battery_Ws/3600/1000)
                From_Battery_Consumption=From_Battery_Consumption+(Cumulated_From_Battery_Ws/3600/1000)
                Cumulated_To_Battery_Ws=0
                Cumulated_From_Battery_Ws=0
                Cumulated_Battery_T=0

        if DeltaT_ACOut !=0:
            Cumulated_ACOut_Ws=Cumulated_ACOut_Ws + ((V1_ACOut + V0_ACOut)/2)*DeltaT_ACOut
            Cumulated_ACOut_T = Cumulated_ACOut_T + DeltaT_ACOut
            V0_ACOut=V1_ACOut
            if Cumulated_ACOut_T>Consumption_Calculation:
                ACOut_Consumption=ACOut_Consumption+(Cumulated_ACOut_Ws/3600/1000)
                Cumulated_ACOut_Ws=0
                Cumulated_ACOut_T=0

            

    #Publishing data on MQTT Server
    client.publish("Grid_Voltage",Grid_Voltage)
    client.publish("Grid_Frequency",Grid_Frequency)
    client.publish("Grid_Energy",Grid_Consumption)

    client.publish("AC_Output_Voltage",AC_Output_Voltage)
    client.publish("AC_Output_Frequency",AC_Output_Frequency)
    client.publish("AC_Output_Current",AC_Output_Current)
    client.publish("AC_Output_Active_Power",AC_Output_Active_Power)
    client.publish("AC_Output_Power",AC_Output_Power)
    client.publish("AC_Output_Energy",ACOut_Consumption)


    client.publish("DC_Voltage",DC_Voltage)
    client.publish("DC_Current",DC_Current)
    client.publish("DC_Power",DC_Power)
    client.publish("DC_Energy_From",From_Battery_Consumption)
    client.publish("DC_Energy_To",To_Battery_Consumption)

    client.publish("PV_Voltage",PV_Voltage)
    client.publish("PV_Current",PV_Current)
    client.publish("PV_Power",PV_Power)
    client.publish("PV_Energy",Solar_Consumption)

    client.publish("Device_Status",Device_Status)

    return


def processQPIGS2(res):
    if debug:
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
    if debug:
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

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

mqttBroker ="127.0.0.1"

client = mqtt.Client("WKS")
client.connect(mqttBroker,1883,60)

#print(sys.argv[0])

now = datetime.datetime.now()
Current_Day=now.strftime("%Y-%m-%d")

if debug:
    print ("flushing buffer...")
    buffer=getResult(5)
    print ("Current date and time : ")
    print (now.strftime("%Y-%m-%d %H:%M:%S"))
    #get device protocol version
    deviceProtocol=getStrData('QPI',1,5)
    print (deviceProtocol)

    #get device serial Number
    deviceSerialNumber=getStrData('QID',1,14)
    print (deviceSerialNumber)

    #get CPU firmware version
    inverterCPUFirmware=getStrData('QVFW',1,15)
    print (inverterCPUFirmware)

    #get SCC1 firmware version
    SCC1Firmware=getStrData('QVFW2',1,16)
    print (SCC1Firmware)

while True:

    #print ("flushing buffer...")
    buffer=getResult(5)


    #get device rating information
    if debug:
        deviceRatingInformation=getStrData('QPIRI',0,98)
        if len(deviceRatingInformation) >= 98 :
            #print('=' * 40)
            #print("QIPRI", len(deviceRatingInformation),deviceRatingInformation)
            #print('=' * 40)
            processQPIRI(deviceRatingInformation)
        else:
            print ("Error QPIRI :")
            print("QIPRI", len(deviceRatingInformation),deviceRatingInformation)
            sys.exit(1)
        #get device Flag status


        #get device warning status
        deviceWarningStatus=getStrData('QPIWS',0,30)
        if len(deviceWarningStatus) >= 30:
            #print('=' * 40)
            #print ("QPIWS",len(deviceWarningStatus),deviceWarningStatus)
            #print('=' * 40)
            processQPIWS(deviceWarningStatus)
        else:
            print ("Error QPIWS :")
            print ("QPIWS",len(deviceWarningStatus),deviceWarningStatus)
            sys.exit(1)
    
    #get device general status
    deviceGeneralStatus=getStrData('QPIGS',0,107)
    if len(deviceGeneralStatus) >= 107:
        #print('=' * 40)
        #print ("QPIGS",len(deviceGeneralStatus),deviceGeneralStatus)
        #print('=' * 40)
        processQPIGS(deviceGeneralStatus,client)
    else:
        print ("Error QPIGS :")
        print ("QPIGS",len(deviceGeneralStatus),deviceGeneralStatus)
        sys.exit(1)

    
    #get device general status
    #deviceGeneralStatus2=getStrData('QPIGS2',0,68)
    #processQPIGS2(deviceGeneralStatus2)

