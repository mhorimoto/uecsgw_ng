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
import queue
import threading

config = configparser.ConfigParser()
config.read('/usr/local/etc/uecsgw/config.ini')

VERSION="3.40"
HOST = ''
PORT = int(config['uecs']['Port'])
TMPD = "/tmp/ckua-"

if (config['mqtt']['Valid']=='yes'):
  MQTTEnable = True
  import paho.mqtt.client as mqtt
else:
  MQTTEnable = False
  
if (config['uecsrelay']['Valid'] == 'yes'):
    UECSrelay = True
    UECSrelayHOST = config['uecsrelay']['host']
    relayTO = (UECSrelayHOST,16520)
else:
    UECSrelay = False

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
# カーネルの受信バッファを大きくして、瞬間的な処理遅延に対する耐性を上げておく
# (根本対策は下のワーカースレッド化だが、念のための保険として増やす)
s.setsockopt(SOL_SOCKET, SO_RCVBUF, 1024*1024)
# uecsrxdump等の他プログラムと16520/udpを共有できるようにする
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
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

# --- uecsconsoleへのPOSTを受信ループから切り離すためのワーカースレッド ---
#
# m304s39〜s54等の実センサーは機器動作状態CCM(cnd)をA-1S-0(1秒ごと)で送信し
# 続けており、以前はrequests.post()をメインの受信ループの中で同期的に呼んで
# いたため、1秒あたりに処理しきれる件数が実際の着信件数を恒常的に下回り、
# recvfrom()の呼び出し間隔が伸びて受信バッファが常時あふれ、CCM全体の
# 約7割が取りこぼされる状態になっていた(tcpdumpでの実測で確認済み)。
#
# 対策として、POST自体は別スレッドのワーカーに投げ、メインループは
# 受信→パース→ログ→リレー送信 という軽い処理だけを行って直ちに次の
# recvfrom()に戻れるようにする。キューが溜まり続ける場合は処理能力不足の
# サインなので、その際はキューの深さをsyslogで警告する。
console_queue = queue.Queue(maxsize=1000)

# requests.post()をワーカーごとに毎回呼ぶと、その都度使い捨てのSessionが
# 作られ、TCP接続の確立とTLSハンドシェイク(鍵交換等の暗号演算)を毎回
# やり直すことになる。OrangePi ONEのような非力なCPUでは、これを複数
# ワーカーで並列に行うとハンドシェイクの演算負荷でCPUを取り合い、
# 肝心のUDP受信ループの方が割を食って逆に取りこぼしが増える現象が
# 実機で確認された。Session1つを全ワーカーで共有してTCP接続を使い回す
# (HTTP keep-alive)ことで、2回目以降はハンドシェイク不要になりCPU負荷が
# 大きく下がる。requests.Session()はスレッドセーフに複数スレッドから
# 使える設計になっている。
_console_session = requests.Session()
if uecsConsoleEnable:
  _console_session.auth = (config['uecsconsole']['User'], config['uecsconsole']['Passwd'])
  CONSOLE_WORKERS = int(config['uecsconsole'].get('Workers', '4'))
  _adapter = requests.adapters.HTTPAdapter(
      pool_connections=CONSOLE_WORKERS, pool_maxsize=CONSOLE_WORKERS
  )
  _console_session.mount('https://', _adapter)
  _console_session.mount('http://', _adapter)

def _uecsconsole_worker():
  while True:
    amac, value, ts = console_queue.get()
    try:
      params = {"M": amac}
      data = {"V": value}
      response = _console_session.post(url, params=params, data=data, timeout=5)
      if response.status_code != 200:
        syslog.syslog(syslog.LOG_WARNING, f"{ts} uecsconsole POST error: {response.status_code}")
    except requests.RequestException as e:
      syslog.syslog(syslog.LOG_WARNING, f"{ts} uecsconsole POST failed/timeout: {e}")
    finally:
      console_queue.task_done()

if uecsConsoleEnable:
  # ワーカー1本だと「1リクエストがtimeout上限の5秒待たされている間、他の
  # 全リクエストが順番待ちする」状態になり、実運用(4台×1秒毎=毎秒4件)では
  # 到底捌ききれずキューが即座に満杯になることが実機で確認された。
  # 複数ワーカーで並列にPOSTすることで、1件の遅延が他をブロックしないようにする。
  # ただし本数を上げすぎるとCPUが非力な機種ではかえって逆効果になり得るため、
  # 既定は控えめな4とし、必要ならconfig.iniの[uecsconsole] Workersで調整する。
  for _ in range(CONSOLE_WORKERS):
    worker = threading.Thread(target=_uecsconsole_worker, daemon=True)
    worker.start()

while True:
  msg, address = s.recvfrom(4096)
  a = datetime.datetime.now()
  d = "{0:4d}/{1:02d}/{2:02d}".format(a.year,a.month,a.day)
  t = "{0:02d}:{1:02d}:{2:02d}".format(a.hour,a.minute,a.second)
  x = "{0}-{1}".format(d,t)
  try:
      msg.decode('utf-8')
  except UnicodeDecodeError as e:
      syslog.syslog(syslog.LOG_WARNING, f"{x} UTF-8デコード失敗: {e}: from={address} msg={msg!r}")
      continue
  try:
      xmlroot  = ET.fromstring(msg)
  except Exception as e:
      # 原因不明のまま握りつぶさず、何が失敗したかを必ずログに残す
      syslog.syslog(syslog.LOG_WARNING, f"{x} XMLパース失敗: {e}: from={address} msg={msg!r}")
      continue
  xdata    = xmlroot.find('DATA')
  if xdata is None:
      syslog.syslog(syslog.LOG_WARNING, f"{x} DATAタグなし(NODESCAN等): from={address} msg={msg!r}")
      continue
  xip      = xmlroot.find('IP')
  if xip is None:
      syslog.syslog(syslog.LOG_WARNING, f"{x} IPタグなし: from={address} msg={msg!r}")
      continue
  value    = xdata.text
  ccmtype  = xdata.get('type')
  room     = xdata.get('room')
  region   = xdata.get('region')
  order    = xdata.get('order')
  priority = xdata.get('priority')
  ipa      = xip.text
  logm     = "{0},{1},{2},{3},{4},{5},{6},{7}".format(x,ccmtype,room,region,order,priority,value,ipa)
  syslog.syslog(syslog.LOG_INFO,logm)

# UECS Relay
# (recvfrom()を再び呼べる状態に一刻も早く戻すため、重い処理より先に済ませる)
  if (UECSrelay):
    s.sendto(msg,relayTO)
#    print(msg.decode())

  if uecsConsoleEnable == True:
    if ipa in hosts_dict:
      amac = hosts_dict[ipa]
      # ここで直接requests.post()を呼ばず、ワーカースレッドにキュー投入するだけ
      # にすることで、uecsconsole側の応答が遅くてもrecvfrom()の呼び出しは
      # 止まらない(=他のCCMの受信・リレーに影響しない)。
      try:
        console_queue.put_nowait((amac, value, x))
      except queue.Full:
        syslog.syslog(syslog.LOG_WARNING, f"{x} uecsconsole送信キューが満杯のため破棄しました(M={amac})")

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

