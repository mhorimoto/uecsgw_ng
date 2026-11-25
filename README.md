# uecsgw_ng

UECS電文を扱うユーティリティ群です。
UECSGWと称したゲートウェイ装置をLinuxベースで構築し、その上で動作するプログラム群です。

This repository provides utility programs to handle UECS protocol messages.
It is intended for building Linux-based "UECS gateway" devices, running multiple small tools for message processing.

***

## 主要プログラム／Main Utility

**recvdata.py**
UECS電文の受信・転送デーモン。受信電文をsyslogへ記録し、MQTT・UECSリレー(UDP転送)・UECS Console(HTTP POST)へ転送します。
A daemon that receives UECS messages, logs them to syslog, and forwards them to MQTT, a UECS relay (UDP) and UECS Console (HTTP POST).

**scanresponder.py**
UECS ノードスキャン(NODESCAN)・通信子スキャン(CCMSCAN)への応答デーモン。UDP 16529 で待ち受け、仕様に従った応答を返します。
A daemon that responds to UECS NODESCAN and CCMSCAN requests on UDP 16529.

***

## ドキュメント／Documentation

- [README-recvdata.md](./README-recvdata.md) 日本語説明書（recvdata.py用）
- [README-recvdata-en.md](./README-recvdata-en.md) English documentation (for recvdata.py)
- [README-scanresponder.md](./README-scanresponder.md) 日本語説明書（scanresponder.py用）

***

## バージョン情報／Version Info

| プログラム名 | バージョン | 備考 |
| :-- | :-- | :-- |
| uecsgw_ng | 0.60 | ユーティリティ全体の呼称 (The overall name of the utility) |
| recvdata.py | 3.40 | 動作安定 (Available) |
| scanresponder.py | 1.00 | 動作安定 (Available) |
| ccmscan.py | 開発中 | under development |
| nodescan.py | 開発中 | under development |
| recvscan.py | 開発中 | under development |


***

## 作者／Author

- 堀本　正文（Masafumi Horimoto）
- mh(at)ys-lab.tech
- YS Lab LCC, Fukuoka, Japan

***

## 日付／Date

- 2025年8月29日 作成 / 2026年11月26日 更新
- Created: August 29, 2025 / Updated: November 26, 2026

***

## ライセンス／License

本ソフトウェアはMITライセンスで配布されます。
This software is distributed under the MIT License.

```
MIT License

Copyright (c) 2025 Masafumi Horimoto

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
