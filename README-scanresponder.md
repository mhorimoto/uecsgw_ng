# SCANRESPONDER.PY (V1.00)

scanresponder.py、設定ファイル(config.ini)、systemdサービスファイルの3点を組み合わせて、UECS ノードスキャン・通信子スキャンへの応答を自動運用します。

## 概要

**scanresponder.py** は、UDP 16529 に届く UECS ノードスキャン要求(NODESCAN)と通信子スキャン要求(CCMSCAN)を受信し、仕様(UECS通信実用規約 Version1.00-E10)に従った応答を返すデーモンです。

| 受信タグ | 応答タグ | 応答内容 |
| :-- | :-- | :-- |
| `<NODESCAN/>` | `<NODE>` | ノード名・ベンダー名・IP・MACアドレス |
| `<CCMSCAN page="N"/>` | `<CCMNUM>` | 発信 CCM 件数（本ゲートウェイは 0 件） |

### 動作上の特徴

- **ポート共有**: `SO_REUSEADDR` を設定しているため、recvscan.py など他のプログラムと 16529/udp を共有できます。
- **IP・MAC 自動検出**: NODESCAN 応答の IP・MAC アドレスは、送信元への経路から使用するインターフェースを自動判定して取得します。複数 NIC 環境でも正しいインターフェースの情報を返します。
- **不正電文の読み飛ばし**: ASCII として読めない電文、XML として解析できない電文、NODESCAN/CCMSCAN タグのない電文は syslog(LOG_WARNING)に記録して無視します。デーモンは停止しません。

## インストール・設定手順

### 1. プログラム・設定ファイルの設置

```sh
sudo cp scanresponder.py /usr/local/bin/scanresponder.py
sudo chmod +x /usr/local/bin/scanresponder.py
```

`config.ini` は recvdata.py と共用します。まだ作成していない場合は `config.ini-sample` を参考に作成してください。

```sh
sudo mkdir -p /usr/local/etc/uecsgw/
sudo cp config.ini-sample /usr/local/etc/uecsgw/config.ini
```

### 2. systemd サービスファイルの設置

```sh
sudo cp scanresponder.service /etc/systemd/system/scanresponder.service
```

### 3. サービス登録・起動

```sh
sudo systemctl daemon-reload
sudo systemctl enable scanresponder.service
sudo systemctl start scanresponder.service
```

- 状態確認: `sudo systemctl status scanresponder.service`
- ログ確認: `journalctl -u scanresponder.service`

## 設定ファイル詳細(config.ini の [uecs] セクション)

| キー | 省略時の既定値 | 説明 |
| :-- | :-- | :-- |
| Version | `1.00-E10` | NODESCAN/CCMSCAN 応答の `ver` 属性値 |
| NodeName | `UECSGW` | NODESCAN 応答の `<NAME>` タグ値 |
| Vender | `uecsgw` | NODESCAN 応答の `<VENDER>` タグ値 |
| UecsId | (省略) | NODESCAN 応答の `<UECSID>` タグ値。省略時はタグごと省略 |

`Version`・`NodeName` は recvdata.py と共用のキーです。`Vender`・`UecsId` は scanresponder.py 専用で、config.ini に記述しない場合は既定値が使われます。

設定例:

```ini
[uecs]
Version = 1.00-E10
NodeName = uecsgw08
Vender = YS-Lab
UecsId = 0123456789
Port = 16520
```

## テスト

`testdata/` ディレクトリに手動テスト用のパケットファイルとスクリプトがあります。

```sh
# 別ターミナルで scanresponder.py を起動しておく
python3 testdata/send_test.py 192.168.x.x
```

テストケース一覧:

| ファイル | 内容 | 期待する動作 |
| :-- | :-- | :-- |
| nodescan_req.xml | NODESCAN 要求 | NODE タグで応答 |
| ccmscan_p1_req.xml | CCMSCAN page=1 要求 | CCMNUM(0件)で応答 |
| ccmscan_p2_req.xml | CCMSCAN page=2 要求 | CCMNUM page=2 total=1 で応答 |
| invalid_xml.txt | 末尾タグが欠けた不正 XML | 応答なし |
| non_uecs.xml | DATA タグのみの電文 | 応答なし |

## 未解決項目

### CCMSCAN で返す CCM 一覧の定義

現状の実装では、CCMSCAN 応答は常に 0 件を返す。これはゲートウェイ自身が DATA CCM を発信しないためだが、CCMSCAN 本来の用途（ノードが発信可能な CCM の一覧を返す）としては不完全である。

**方針（未実装）**: `config.ini` に `[ccm*]` セクションを追加し、発信する CCM を列挙する方式で実装する。

```ini
# 設定例（未実装）
[ccm0]
type = InAirTemp.mIC
room = 1
region = 1
order = 1
priority = 1
cast = 1
unit = C
SR = S
LV = A-10S-0
```

CCMSCAN 応答の `<CCM>` タグに必要な属性は No/room/region/order/priority/cast/unit/SR/LV。
パケットサイズ上限(480 byte)を超える場合はページ分割が必要。

## 参考：各ファイルの役割

| ファイル名 | 役割 |
| :-- | :-- |
| scanresponder.py | NODESCAN/CCMSCAN 応答デーモン本体 |
| config.ini | 動作設定（`/usr/local/etc/uecsgw/`、recvdata.py と共用） |
| config.ini-sample | config.ini の雛形 |
| scanresponder.service | systemd サービスユニットファイル |
| testdata/ | 手動テスト用パケットファイルとスクリプト |
