#! /opt/rh/rh-python36/root/usr/bin/python

import netifaces
from socket import *

HOST = netifaces.ifaddresses('enp1s0')[netifaces.AF_INET][0]['addr']
ADDRESS = netifaces.ifaddresses('enp1s0')[netifaces.AF_INET][0]['broadcast']
PORT = 16529

print("ADDRESS={0}".format(ADDRESS))
print("HOST={0}".format(HOST))
s = socket(AF_INET,SOCK_DGRAM)
s.setsockopt(SOL_SOCKET,SO_REUSEADDR|SO_BROADCAST,1)
#s.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
s.bind((HOST,PORT))

msg = "<?xml version=\"1.0\"?><UECS ver=\"1.00-E10\"><NODESCAN/></UECS>"

s.sendto(msg.encode(),(ADDRESS,PORT))
s.close()
