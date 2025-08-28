#! /usr/bin/env python3
#coding: utf-8
#
from socket import *
import sys
import os
import datetime
import time
import syslog
import requests
import xml.etree.ElementTree as ET
import configparser

config = configparser.ConfigParser()
config.read('/usr/local/etc/uecsgw/config.ini')

VERSION="3.10"
HOST = ''
PORT = int(config['uecs']['Port'])
TMPD = "/tmp/ckua-"

if (config['mqtt']['Valid']!='no'):
  MQTTEnable = True
  import paho.mqtt.client as mqtt
else:
  MQTTEnable = False
  
if (config['uecsconsole']['Valid'] != 'no'):
  uecsConsoleEnable = True
  url = config['uecsconsole']['url']
  hosts_dict = {}
  for section in config.sections():
    if section.startswith('m304'):
        aip = config[section]['ip']
        aid = config[section]['id']
        mac = config[section]['mac'].upper()
        name= section
        hosts_dict[aip] = mac
else:
  uecsConsoleEnable = False

s = socket(AF_INET,SOCK_DGRAM)
s.bind((HOST,PORT))
a = datetime.datetime.now()
d = "{0:4d}/{1:02d}/{2:02d}".format(a.year,a.month,a.day)
t = "{0:02d}:{1:02d}:{2:02d}".format(a.hour,a.minute,a.second)
x = "{0}-{1}".format(d,t)
syslog.syslog(syslog.LOG_INFO,"{0} START UECS recvdata.py VER.{1}".format(x,VERSION))

if (MQTTEnable):
  print("MQTT start")
  hn = config['mqtt']['Id']
  client = mqtt.Client(hn)
  client.username_pw_set(config['mqtt']['User'],config['mqtt']['Passwd'])
  client.connect(config['mqtt']['BrokerHost'],int(config['mqtt']['Port']), 60) 
  client.loop_start()
else:
  print("MQTT not enable")

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
  if ipa in hosts_dict:
    amac = hosts_dict[ipa]
    params = {"M":amac}
    data = {
      "V":value
    }
#    print(params,data)
    try:
      response = requests.post(url,params=params,data=data)
      if response.status_code == 200:
        pass
      else:
        print(f"error")
    except requests.RequestException as e:
        print(f"Request error: {e}")
        

#  if (ccmtype=='WRadiation'):
  if (MQTTEnable):
    topictop = config['mqtt']['TopicTop']
    pubtopic = "{0}/data/{1}/{2}/{3}/{4}/{5}".format(topictop,room,region,order,ccmtype,ipa)
    client.publish(pubtopic,value)
# endif
  SMPF = TMPD+ipa+".chk"
  if (os.path.exists(SMPF)):
    os.remove(SMPF)

s.close()
sys.quit()

