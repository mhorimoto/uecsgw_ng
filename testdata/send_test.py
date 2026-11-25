#!/usr/bin/env python3
# coding: utf-8
#
# testdata/send_test.py
#
# scanresponder.py の手動テスト用スクリプト。
# testdata/ 内の各ファイルを UDP 16529 に送り、応答を表示する。
#
# 使い方:
#   # 別ターミナルで scanresponder.py を起動しておく
#   python3 testdata/send_test.py [host]
#
# host を省略すると 127.0.0.1 に送信する。
#
import socket
import sys
import os
import time

HOST    = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
PORT    = 16529
TIMEOUT = 2.0

TESTDIR = os.path.dirname(os.path.abspath(__file__))

CASES = [
    ('nodescan_req.xml',   '正常: NODESCAN 要求',          True),
    ('ccmscan_p1_req.xml', '正常: CCMSCAN page=1 要求',     True),
    ('ccmscan_p2_req.xml', '正常: CCMSCAN page=2 (範囲外)', True),
    ('invalid_xml.txt',    '異常: 壊れた XML',              False),
    ('non_uecs.xml',       '異常: DATA タグのみ (無視)',     False),
]

def send_and_recv(data: bytes) -> str | None:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(TIMEOUT)
    try:
        s.sendto(data, (HOST, PORT))
        resp, _ = s.recvfrom(512)
        return resp.decode('ascii')
    except socket.timeout:
        return None
    finally:
        s.close()

def main():
    print(f'送信先: {HOST}:{PORT}\n{"="*50}')
    for filename, label, expect_reply in CASES:
        path = os.path.join(TESTDIR, filename)
        if not os.path.exists(path):
            print(f'[SKIP] {label}: ファイルなし ({filename})')
            continue

        with open(path, 'rb') as f:
            data = f.read().rstrip(b'\n')

        print(f'\n[CASE] {label}')
        print(f'  送信 ({len(data)} bytes): {data[:80].decode("ascii", errors="replace")}')

        resp = send_and_recv(data)
        if resp:
            print(f'  応答:\n' + '\n'.join('    ' + line for line in resp.splitlines()))
            if not expect_reply:
                print('  ** 応答が来たが期待は「無視」 **')
        else:
            print(f'  応答なし (timeout {TIMEOUT}s)')
            if expect_reply:
                print('  ** 応答が来るはずなのに来ていない **')

        time.sleep(0.1)

if __name__ == '__main__':
    main()
