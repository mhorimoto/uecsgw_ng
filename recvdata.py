#! /usr/bin/env python3
#coding: utf-8
#
from socket import *
import sys
import os
import datetime
import time
import syslog
import xml.etree.ElementTree as ET

VERSION="1.00"
HOST = ''
PORT = 16520
LOGF = "/var/log/uecs/recvdata.log"
TMPD = "/tmp/ckua-"

#try:
#  lgf = open(LOGF,'a',1)   # line buffering
#except:
#  print("Can not open logfile {0}".format(lgf))
#  quit()

s = socket(AF_INET,SOCK_DGRAM)
s.bind((HOST,PORT))
a=datetime.datetime.now()
d = "{0:4d}/{1:02d}/{2:02d}".format(a.year,a.month,a.day)
t = "{0:02d}:{1:02d}:{2:02d}".format(a.hour,a.minute,a.second)
x = "{0}-{1}".format(d,t)
syslog.syslog(syslog.LOG_INFO,"{0} START UECS recvdata.py VER.{1}".format(x,VERSION))
#lgf.write("\n{0} START UECS recvdata.py VER.{1}\n".format(x,VERSION))

while True:
  msg, address = s.recvfrom(4096)
  a=datetime.datetime.now()
  d="{0:4d}/{1:02d}/{2:02d}".format(a.year,a.month,a.day)
  t="{0:02d}:{1:02d}:{2:02d}".format(a.hour,a.minute,a.second)
  x="{0}-{1}".format(d,t)
  # <?xml version="1.0"?><UECS ver="1.00-E10">
  txt = msg.decode()
#  txt = txt.replace('</DATA><IP>',',')
#  txt = txt.replace('</IP></UECS>','')
#  txt = txt.replace('<?xml version="1.0"?><UECS ver="1.00-E10">','')
#  lgf.write("{0} {1}\n".format(x,msg.decode()))
  xmlroot = ET.fromstring(msg)
  xdata = xmlroot.find('DATA')
  value = xdata.text
  ccmtype = xdata.get('type')
  room = xdata.get('room')
  region = xdata.get('region')
  order = xdata.get('order')
  priority = xdata.get('priority')
  ipa = xmlroot.find('IP').text
  logm = "{0},{1},{2},{3},{4},{5},{6},{7}".format(x,ccmtype,room,region,order,priority,value,ipa)
  syslog.syslog(syslog.LOG_INFO,logm)

  SMPF=TMPD+ipa+".chk"
  if (os.path.exists(SMPF)):
    print("remove "+SMPF)
    os.remove(SMPF)

#lgf.close()
s.close()
sys.quit()

