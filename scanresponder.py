#!/usr/bin/env python3
# coding: utf-8
#
# scanresponder.py - UECS NODESCAN/CCMSCAN responder (V1.00)
#
# Listens on UDP 16529 and responds to NODESCAN and CCMSCAN requests.
# This gateway publishes no DATA CCMs of its own, so CCMSCAN responses
# report 0 entries.
#
from socket import *
import sys
import syslog
import xml.etree.ElementTree as ET
import configparser

CONFIG_PATH = '/usr/local/etc/uecsgw/config.ini'
SCAN_PORT   = 16529
VERSION     = "1.00"


def local_ip_for(dest_ip):
    """Return the local IP address that would be used to reach dest_ip."""
    with socket(AF_INET, SOCK_DGRAM) as s:
        s.connect((dest_ip, 1))
        return s.getsockname()[0]


def mac_for_ip(ip):
    """Return MAC address (12 hex chars, no colons) for the interface with ip."""
    try:
        import subprocess
        out = subprocess.run(
            ['ip', '-o', 'addr', 'show'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).stdout.decode()
        for line in out.splitlines():
            parts = line.split()
            # format: idx iface inet addr/prefix ...
            if len(parts) >= 4 and parts[2] == 'inet':
                if parts[3].split('/')[0] == ip:
                    iface = parts[1]
                    with open(f'/sys/class/net/{iface}/address') as f:
                        return f.read().strip().replace(':', '').upper()
    except Exception:
        pass
    return '000000000000'


def node_response(cfg, local_ip, local_mac):
    ver    = cfg['uecs'].get('Version',  '1.00-E10')
    name   = cfg['uecs'].get('NodeName', 'UECSGW')
    vender = cfg['uecs'].get('Vender',   'uecsgw')
    uecsid = cfg['uecs'].get('UecsId',   '')

    lines = [
        '<?xml version="1.0"?>',
        f'<UECS ver="{ver}">',
        '<NODE>',
        f'<NAME>{name}</NAME>',
        f'<VENDER>{vender}</VENDER>',
    ]
    if uecsid:
        lines.append(f'<UECSID>{uecsid}</UECSID>')
    lines += [
        f'<IP>{local_ip}</IP>',
        f'<MAC>{local_mac}</MAC>',
        '</NODE>',
        '</UECS>',
    ]
    return '\n'.join(lines) + '\n'


def ccmnum_response(cfg, page):
    ver = cfg['uecs'].get('Version', '1.00-E10')
    return (
        '<?xml version="1.0"?>\n'
        f'<UECS ver="{ver}">\n'
        f'<CCMNUM page="{page}" total="1">0</CCMNUM>\n'
        '</UECS>\n'
    )


def main():
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_PATH)

    syslog.openlog('scanresponder', syslog.LOG_PID, syslog.LOG_DAEMON)
    syslog.syslog(syslog.LOG_INFO,
                  f'START scanresponder.py VER.{VERSION}')

    s = socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind(('', SCAN_PORT))

    while True:
        try:
            raw, addr = s.recvfrom(512)
        except OSError as e:
            syslog.syslog(syslog.LOG_ERR, f'recvfrom: {e}')
            break

        try:
            text = raw.decode('ascii')
        except UnicodeDecodeError:
            syslog.syslog(syslog.LOG_WARNING,
                          f'non-ASCII packet from {addr[0]}')
            continue

        try:
            root = ET.fromstring(text)
        except ET.ParseError as e:
            syslog.syslog(syslog.LOG_WARNING,
                          f'XML parse error from {addr[0]}: {e}')
            continue

        if root.find('NODESCAN') is not None:
            local_ip  = local_ip_for(addr[0])
            local_mac = mac_for_ip(local_ip)
            resp = node_response(cfg, local_ip, local_mac)
            s.sendto(resp.encode('ascii'), addr)
            syslog.syslog(syslog.LOG_INFO,
                          f'NODESCAN from {addr[0]} -> replied as {local_ip}')

        elif root.find('CCMSCAN') is not None:
            elem = root.find('CCMSCAN')
            page = elem.get('page', '1')
            resp = ccmnum_response(cfg, page)
            s.sendto(resp.encode('ascii'), addr)
            syslog.syslog(syslog.LOG_INFO,
                          f'CCMSCAN page={page} from {addr[0]} -> replied')

    s.close()


if __name__ == '__main__':
    main()
