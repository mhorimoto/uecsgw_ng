# RECVDATA.PY

recvdata.py、設定ファイル、systemdサービスファイルの3点を組み合わせて、UECS電文の受信・転送を自動運用します。[^1][^2][^3]

## 概要

**recvdata.py**は、UDPでブロードキャストされるUECS電文を受信し、syslog記録、MQTTブローカー、HTTP POST転送（UECS Console）を行うデーモンプログラムです。**config.ini**で伝送先やトピックなど各種詳細設定を柔軟に変更できます。[^2][^1]

## インストール・設定手順

### 1. プログラム・設定ファイルの設置

- `recvdata.py` を `/usr/local/bin/recvdata.py` として設置・実行権限付与
- `config.ini-sample` を `/usr/local/etc/uecsgw/config.ini` にコピーし、設定内容を使用環境に合わせて編集[^2]

```sh
sudo cp recvdata.py /usr/local/bin/recvdata.py
sudo chmod +x /usr/local/bin/recvdata.py
sudo mkdir -p /usr/local/etc/uecsgw/
sudo cp config.ini-sample /usr/local/etc/uecsgw/config.ini
```


### 2. 必要パッケージのインストール

```sh
pip install paho-mqtt requests
```

- MQTT連携が不要な場合でも `requests` は必須です。


### 3. systemdサービスファイルの設置

- `recvdata.service` を `/etc/systemd/system/recvdata.service` に配置[^3]

```sh
sudo cp recvdata.service /etc/systemd/system/recvdata.service
```


### 4. systemdでサービス登録・起動

```sh
sudo systemctl daemon-reload
sudo systemctl enable recvdata.service
sudo systemctl start recvdata.service
```

- サービスの状態確認

```sh
sudo systemctl status recvdata.service
```

- ログの確認

```sh
journalctl -u recvdata.service
```


## 設定ファイル詳細

- **[uecs]**: 受信ポートやルーム・リージョン・ノード名などUECSプロトコル基本設定
- **[mqtt]**: MQTT連携要素（Valid=yesで有効）
- **[uecsconsole]**: HTTP POST連携（Valid=yesで有効）
- **[m304]**: 管理対象ノード情報[^2]


## 参考：各ファイルの役割

| ファイル名 | 役割 |
| :-- | :-- |
| recvdata.py | UECS電文受信・転送本体 |
| config.ini | 動作/転送先等の各種設定 |
| recvdata.service | systemdサービスユニットファイル |


***

このセットアップにより、システム起動時に自動的にデーモンが立ち上がり、UECSネットワークからの電文受信・転送が常時行われます。[^1][^3][^2]

<div style="text-align: center">⁂</div>

[^1]: recvdata.py

[^2]: config.ini-sample

[^3]: recvdata.service

