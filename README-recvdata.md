# RECVDATA.PY (V3.40)

recvdata.py、設定ファイル、systemdサービスファイルの3点を組み合わせて、UECS電文の受信・転送を自動運用します。

## 概要

**recvdata.py**は、UDPで送信されるUECS電文(既定ポート16520/udp)を受信し、次の処理を行うデーモンです。転送先ごとに `config.ini` で有効/無効を切り替えます。

1. **syslog記録**(常時): `日時,type,room,region,order,priority,値,送信元IP` のCSV形式でLOG_INFOに記録します。
2. **UECSリレー**(`[uecsrelay]`): 受信した電文をそのまま別ホストの16520/udpへ転送します。
3. **UECS Console**(`[uecsconsole]`): `[m304*]` に登録したIPからの電文の値を、HTTP POSTで送信します(Basic認証)。
4. **MQTT**(`[mqtt]`): `TopicTop/data/room/region/order/type/IP` のトピックに値をpublishします。

### 動作上の特徴

- **ポート共有**: `SO_REUSEADDR` を設定しているため、uecsrxdump など他のプログラムと16520/udpを共有できます。
- **不正電文の読み飛ばし**: UTF-8として読めない電文、XMLとして解析できない電文、DATAタグまたはIPタグのない電文(NODESCANなど)は、LOG_WARNINGをsyslogに記録して読み飛ばします。デーモンは停止しません。
- **受信取りこぼし対策**: UECS ConsoleへのPOSTは別スレッドのワーカー(既定4本、キュー上限1000件)で行い、受信ループを止めません。キューが満杯になった場合は破棄してsyslogに警告します。HTTP接続(keep-alive)は全ワーカーで共有します。受信バッファは1MiBに拡大しています。
- **一時ファイル削除**: 受信の都度、`/tmp/ckua-<IP>.chk` が存在すれば削除します。

## インストール・設定手順

### 1. プログラム・設定ファイルの設置

- `recvdata.py` を `/usr/local/bin/recvdata.py` として設置し、実行権限を付与
- `config.ini-sample` を `/usr/local/etc/uecsgw/config.ini` にコピーし、環境に合わせて編集

```sh
sudo cp recvdata.py /usr/local/bin/recvdata.py
sudo chmod +x /usr/local/bin/recvdata.py
sudo mkdir -p /usr/local/etc/uecsgw/
sudo cp config.ini-sample /usr/local/etc/uecsgw/config.ini
```

`config.ini` にはUECS Consoleの認証情報やMQTTのパスワードが入るため、必要に応じて所有者・権限を絞ってください(例: `sudo chmod 600 /usr/local/etc/uecsgw/config.ini`)。

### 2. 必要パッケージのインストール

```sh
pip install requests paho-mqtt
```

- `requests` は常に必須です(import しています)。
- `paho-mqtt` は `[mqtt]` の `Valid = yes` のときだけ必要です。

### 3. systemdサービスファイルの設置

```sh
sudo cp recvdata.service /etc/systemd/system/recvdata.service
```

### 4. サービス登録・起動

```sh
sudo systemctl daemon-reload
sudo systemctl enable recvdata.service
sudo systemctl start recvdata.service
```

- 状態確認: `sudo systemctl status recvdata.service`
- ログ確認: `journalctl -u recvdata.service`(電文のログはsyslogにも出力されます)

## 設定ファイル詳細(config.ini)

| セクション | キー | 説明 |
| :-- | :-- | :-- |
| `[uecs]` | Port | 受信するUDPポート(通常 16520)。他に Version, Room, Region, Order, NodeName |
| `[mqtt]` | Valid | `yes` のときだけ有効 |
| | TopicTop, BrokerHost, Port, User, Passwd, Id | MQTTブローカーの接続・トピック設定 |
| `[uecsrelay]` | Valid | `yes` のときだけ有効 |
| | host | 転送先ホスト(転送先ポートは16520固定) |
| `[uecsconsole]` | Valid | **`no` 以外**で有効(`yes` 以外ではなく、`no` のときだけ無効) |
| | url | POST先URL |
| | User, Passwd | Basic認証のユーザー名・パスワード(有効時は必須。無いと起動時にエラー) |
| | Workers | POSTワーカー数(省略時 4) |
| `[m304*]` | id, ip, mac | UECS Consoleへ送る機器の対応表。セクション名が `m304` で始まるものを全て読み込み、`ip` からの電文を `mac`(大文字化)宛として送信 |

- `[mqtt]` と `[uecsrelay]` と `[uecsconsole]` の3セクションは、無効でも**存在している必要があります**(`Valid` を読むため)。
- `[uecsconsole]` の `Valid` は他と判定が逆なので注意してください。無効にするときは必ず `Valid = no` と書きます。

## 参考：各ファイルの役割

| ファイル名 | 役割 |
| :-- | :-- |
| recvdata.py | UECS電文受信・転送本体 |
| config.ini | 動作/転送先等の各種設定(`/usr/local/etc/uecsgw/`) |
| config.ini-sample | config.ini の雛形 |
| recvdata.service | systemdサービスユニットファイル |
| recvdata-rotation.sh | ログのローテーション用スクリプト例(別途 `uecsrxd-insert.py` が必要) |
