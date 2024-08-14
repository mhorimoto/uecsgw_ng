#! /opt/rh/rh-python36/root/usr/bin/python
# -*- coding: utf-8 -*-

from socket import *
import sys
import xml.etree.ElementTree as ET

TARGETHOST = sys.argv[1]
PAGE = 1
PORT = 16529

s = socket(AF_INET,SOCK_DGRAM)
#s.setsockopt(SOL_SOCKET,)
s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
s.bind(('192.168.0.66',PORT))

ccmmsg = "<?xml version=\"1.0\"?><UECS ver=\"1.00-E10\"><CCMSCAN page=\"{0}\"/></UECS>"
msg = ccmmsg.format(PAGE)

s.sendto(msg.encode(),(TARGETHOST,PORT))
rxmsg,rxaddr = s.recvfrom(512)

root = ET.fromstring(rxmsg.decode())
for ccmnum in root.findall('CCMNUM'):
    total = ccmnum.get('total')
    page  = ccmnum.get('page')
    ccmcnt= ccmnum.text

    # print("page/total/count={0}/{1}/{2}".format(page,total,ccmcnt))

    # <?xml version="1.0"?>
    #  <UECS ver="1.00-E10">
    #   <CCMNUM page="1" total="23">2</CCMNUM>
    #   <CCM No="0" room="1" region="1" order="1" priority="1" cast="0" unit="" SR="S" LV="A-1S-0">cnd.cMC</CCM>
    #   <CCM No="1" room="1" region="1" order="1" priority="1" cast="1" unit="C" SR="S" LV="A-10S-0">InAirTemp.cMC</CCM>
    #  </UECS>
    for ccm in root.findall('CCM'):
        no       = ccm.get('No')
        room     = ccm.get('room')
        region   = ccm.get('region')
        order    = ccm.get('order')
        priority = ccm.get('priority')
        cast     = ccm.get('cast')
        unit     = ccm.get('unit')
        sr       = ccm.get('SR')
        lv       = ccm.get('LV')
        txt      = ccm.text
        print("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}".format(no,room,region,order,priority,cast,unit,sr,lv,txt))

for ccmix in range(2,int(total)):
    msg = ccmmsg.format(ccmix)
    s.sendto(msg.encode(),(TARGETHOST,PORT))
    rxmsg,rxaddr = s.recvfrom(512)
    root = ET.fromstring(rxmsg.decode())
    for ccm in root.findall('CCM'):
        no       = ccm.get('No')
        room     = ccm.get('room')
        region   = ccm.get('region')
        order    = ccm.get('order')
        priority = ccm.get('priority')
        cast     = ccm.get('cast')
        unit     = ccm.get('unit')
        sr       = ccm.get('SR')
        lv       = ccm.get('LV')
        txt      = ccm.text
        print("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}".format(no,room,region,order,priority,cast,unit,sr,lv,txt))


s.close()
