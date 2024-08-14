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
import paho.mqtt.client as mqtt
import configparser

config = configparser.ConfigParser()
config.read('/usr/local/etc/uecsgw/config.ini')

VERSION="3.00"
HOST = ''
PORT = int(config['uecs']['Port'])
print(PORT)
TMPD = "/tmp/ckua-"

s = socket(AF_INET,SOCK_DGRAM)
s.bind((HOST,PORT))
a = datetime.datetime.now()
d = "{0:4d}/{1:02d}/{2:02d}".format(a.year,a.month,a.day)
t = "{0:02d}:{1:02d}:{2:02d}".format(a.hour,a.minute,a.second)
x = "{0}-{1}".format(d,t)
syslog.syslog(syslog.LOG_INFO,"{0} START UECS recvdata.py VER.{1}".format(x,VERSION))
hn     = config['mqtt']['Id']
client = mqtt.Client(hn)
client.username_pw_set(config['mqtt']['User'],config['mqtt']['Passwd'])
client.connect(config['mqtt']['BrokerHost'],int(config['mqtt']['Port']), 60) 
client.loop_start()

while True:
  msg, address = s.recvfrom(4096)
  a = datetime.datetime.now()
  d = "{0:4d}/{1:02d}/{2:02d}".format(a.year,a.month,a.day)
  t = "{0:02d}:{1:02d}:{2:02d}".format(a.hour,a.minute,a.second)
  x = "{0}-{1}".format(d,t)
  txt      = msg.decode()
  xmlroot  = ET.fromstring(msg)
  xdata    = xmlroot.find('DATA')
  value    = xdata.text
  ccmtype  = xdata.get('type')
  room     = xdata.get('room')
  region   = xdata.get('region')
  order    = xdata.get('order')
  priority = xdata.get('priority')
  ipa      = xmlroot.find('IP').text
  logm     = "{0},{1},{2},{3},{4},{5},{6},{7}".format(x,ccmtype,room,region,order,priority,value,ipa)
  syslog.syslog(syslog.LOG_INFO,logm)
  if (ccmtype=='WRadiation'):
    topictop = config['mqtt']['TopicTop']
    pubtopic = "{0}/data/{1}/{2}/{3}/{4}".format(topictop,room,region,order,ccmtype)
    client.publish(pubtopic,value)

  SMPF = TMPD+ipa+".chk"
  if (os.path.exists(SMPF)):
    os.remove(SMPF)

s.close()
sys.quit()

