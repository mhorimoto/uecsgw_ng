# HANDOFF — wip/scan-responder

作成日: 2026-11-25 / 最終更新: 2026-11-26 / ブランチ: `wip/scan-responder`(main の ed5f5be から分岐)

## 現状(重要)

`scanresponder.py` V1.00 を実装・実機確認済み。**未コミット**。
次のセッションの主タスクは CCMSCAN で返す CCM 一覧の実装（`config.ini` の `[ccm*]` セクションから読む方式）。

## 実装済み

| ファイル | 状態 | 内容 |
| :-- | :-- | :-- |
| `scanresponder.py` (V1.00) | 未コミット | NODESCAN/CCMSCAN 応答デーモン本体 |
| `scanresponder.service` | 未コミット | systemd ユニットファイル |
| `README-scanresponder.md` | 未コミット | 説明書（未解決項目セクションあり） |
| `testdata/` | 未コミット | テスト用パケットファイルと send_test.py |
| `config.ini-sample` | 未コミット | `[uecs]` に Vender/UecsId のコメント例を追記 |
| `README.md` | 未コミット | scanresponder.py を追加、バージョンを 0.60 に更新 |
| `.gitignore` | 未コミット | `__pycache__/` を追加 |
| `HANDOFF.md` | 未コミット | 本ファイル |

### インストール手順(実機)
```
install -m 755 scanresponder.py /usr/local/bin/
install -m 644 scanresponder.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now scanresponder
```

### 実機確認(2026-11-26, opinas01 / 192.168.38.99)

- NODESCAN 応答: NAME=opinas01, VENDER=YS-Lab, UECSID=0123456789, IP=192.168.38.99, MAC=9CB654AE567E ✓
- CCMSCAN page=1 応答: CCMNUM page=1 total=1 0件 ✓
- CCMSCAN page=2 応答: CCMNUM page=2 total=1 0件 ✓
- 壊れた XML: 応答なし ✓
- DATA タグのみ: 応答なし ✓

### 修正履歴

- `mac_for_ip()`: `subprocess.run(..., capture_output=True)` は Python 3.6 非対応のため
  `stdout=subprocess.PIPE, stderr=subprocess.PIPE` + `.decode()` に変更。

## 次のタスク(優先順)

### 1. CCMSCAN で返す CCM 一覧の実装【次回メインタスク】

**方針**: `config.ini` に `[ccm*]` セクションを追加し、発信する CCM を列挙する。

```ini
# 設定例
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

実装のポイント:
- `scanresponder.py` 起動時に `config.ini` の `[ccm*]` セクションを全て読み込む
- CCMSCAN 応答時に CCM 一覧を `<CCM No="N" ...>type</CCM>` 形式で返す
- 1パケット 480 byte 上限を超える場合はページ分割（`total` を複数ページ）
- `testdata/ccmscan_p1_req.xml` / `ccmscan_p2_req.xml` でページ分割のテストが可能

詳細は `README-scanresponder.md` の「未解決項目」セクションも参照。

### 2. その他の残作業

- 既存スクリプトの固定値(NIC 名・IP・shebang)を `config.ini` 化または引数化する。
- `recvscan.py` の不具合修正:
  - `msg == "."` は bytes vs str 比較で常に偽 → `msg == b"."`
  - `except` ブロックで未定義の `lgf` を参照 → `LOGF` に変更

## 未解決の疑問

- `recvdata.py` の受信した NODESCAN をリレー先へ流すべきか(現状は読み飛ばし)。
- `recvdata-rotation.sh` が呼ぶ `uecsrxd-insert.py` の所在(リポジトリに無い)。
- 過去に `config.ini` 直書きだった認証情報が git 履歴に残っている。パスワードを使い回しているなら変更する。

## 参考: UECS ポート割り当て

| ポート | 用途 |
| :-- | :-- |
| UDP 16520 | CCM データ送受信 (`recvdata.py`) |
| UDP 16521 | 提供者サーチ(SEARCH/SERVER) |
| UDP 16522〜16528 | 予約 |
| UDP 16529 | ノード/通信子スキャン (`scanresponder.py`, `recvscan.py`) |
