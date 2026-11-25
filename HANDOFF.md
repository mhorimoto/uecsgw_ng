# HANDOFF — wip/scan-responder

作成日: 2026-11-25 / ブランチ: `wip/scan-responder`(main の ed5f5be から分岐)

## 現状(重要)

- 引き継ぎ時点で **作業ツリーはクリーン**で、NODESCAN / CCMSCAN **応答スクリプトの作業中の変更は存在しなかった**。
  このブランチのコミットは本ファイルだけ。応答スクリプトが未保存・別マシン・別ブランチ(`devel` 等)にある場合は、
  そちらから取り込む必要がある。
- リポジトリにある `nodescan.py` / `ccmscan.py` / `recvscan.py` は **スキャンを送る/結果を受ける側**であり、
  NODESCAN / CCMSCAN に **応答する側ではない**。

## 調査結果(このセッションで確認できたこと)

- `recvdata.py`(V3.30)は 16520/udp で CCM 電文を受信し、syslog・UECS リレー・MQTT・UECS Console へ転送する。
  main に反映済み・実機(uecsgw08)で動作確認済み。
  - `SO_REUSEADDR` 設定済み(uecsrxdump 等と 16520/udp を共有可)。
  - DATA/IP タグなし(NODESCAN 等)・UTF-8 不正・XML 不正の電文は LOG_WARNING で読み飛ばす。
  - UECS Console の Basic 認証は `config.ini` の `[uecsconsole] User / Passwd` から読む。
- 既存スキャン系スクリプトの現状(いずれも未整備):
  - `nodescan.py`: NODESCAN をブロードキャストで送るだけ。NIC 名 `enp1s0` と
    shebang `/opt/rh/rh-python36/...` が固定(RHEL 系前提)。
  - `ccmscan.py`: 引数のホストへ CCMSCAN(page=1 固定)を送り応答を解析。
    バインド IP が `192.168.0.66` に固定。
  - `recvscan.py`: 16529/udp で受信してログへ。`msg == "."` は bytes と str の比較で常に偽、
    エラーメッセージが未定義の `lgf` を参照している(Python3 では不具合)。
  - スキャン用ポートは **16529/udp**(通常 CCM の 16520 とは別)。

## 決まった設計

- 設計として確定したものはまだない(応答スクリプトの設計メモは未受領)。
- 方針案(未承認): `recvdata.py` とは別プロセスの応答デーモンとし、16529/udp で
  NODESCAN / CCMSCAN を受けて応答する。設定は `config.ini` を共有し、`[uecs]` の
  Version / Room / Region / Order / NodeName を応答内容に使う。

## 残りの作業

1. 応答スクリプトの作業中ファイルの所在を確認し、このブランチに取り込む。
2. NODESCAN / CCMSCAN の応答電文仕様を UECS 仕様書で確認する
   (NODESCAN 応答の NODE 属性、CCMSCAN の CCMNUM と page 分割、CCM 一覧の項目など)。
3. 応答デーモンを実装(systemd ユニットは `recvscan.service` を参考に)。
4. 既存スクリプトの固定値(NIC 名・IP・shebang)を `config.ini` 化または引数化する。
5. `recvscan.py` の不具合(上記)の修正。
6. 実機で確認し、README とバージョン表(README.md の「開発中」)を更新する。

## 未解決の疑問

- 応答する CCM の一覧はどこから得るか(`[m304*]` の設定か、受信実績からの自動収集か)。
- 16529/udp と 16520/udp を同一プロセスで扱うか、別プロセスにするか。
- `recvdata.py` の受信した NODESCAN をリレー先へ流すべきか(現状は読み飛ばしでリレーもされない)。
- 対象の動作環境は RHEL 系(shebang)か Debian 系(uecsgw08)か。
- `recvdata-rotation.sh` が呼ぶ `uecsrxd-insert.py` の所在(リポジトリに無い)。
- 過去に `config.ini` 直書きだった認証情報が git 履歴に残っている。パスワードを使い回しているなら変更する。
