# recvdata.py README (V3.40)

recvdata.py, its config file and the systemd unit file together provide unattended receiving and forwarding of UECS messages.

## Overview

**recvdata.py** is a daemon that receives UECS messages sent over UDP (default port 16520/udp) and does the following. Each destination is switched on or off in `config.ini`.

1. **syslog logging** (always): logs `datetime,type,room,region,order,priority,value,sender-IP` as CSV at LOG_INFO.
2. **UECS relay** (`[uecsrelay]`): forwards the received message unchanged to port 16520/udp of another host.
3. **UECS Console** (`[uecsconsole]`): sends the value of messages from the IPs listed in `[m304*]` sections by HTTP POST (Basic auth).
4. **MQTT** (`[mqtt]`): publishes the value to `TopicTop/data/room/region/order/type/IP`.

### Behavior notes

- **Port sharing**: `SO_REUSEADDR` is set, so 16520/udp can be shared with other programs such as uecsrxdump.
- **Bad messages are skipped**: messages that are not valid UTF-8 or XML, or that lack a DATA or IP tag (e.g. NODESCAN), are logged to syslog at LOG_WARNING and skipped. The daemon does not stop.
- **Avoiding packet loss**: HTTP POSTs to UECS Console run in worker threads (4 by default, queue limit 1000) so the receive loop is never blocked. If the queue is full, messages are dropped with a syslog warning. The HTTP connection (keep-alive) is shared by all workers, and the receive buffer is enlarged to 1 MiB.
- **Temp file cleanup**: on every message, `/tmp/ckua-<IP>.chk` is removed if it exists.

## Installation and Setup

### 1. Install the program and config file

- Place `recvdata.py` at `/usr/local/bin/recvdata.py` and make it executable.
- Copy `config.ini-sample` to `/usr/local/etc/uecsgw/config.ini` and edit it for your environment.

```sh
sudo cp recvdata.py /usr/local/bin/recvdata.py
sudo chmod +x /usr/local/bin/recvdata.py
sudo mkdir -p /usr/local/etc/uecsgw/
sudo cp config.ini-sample /usr/local/etc/uecsgw/config.ini
```

`config.ini` holds the UECS Console credentials and the MQTT password, so restrict its permissions if needed (e.g. `sudo chmod 600 /usr/local/etc/uecsgw/config.ini`).

### 2. Install Python packages

```sh
pip install requests paho-mqtt
```

- `requests` is always required (it is imported unconditionally).
- `paho-mqtt` is required only when `[mqtt]` has `Valid = yes`.

### 3. Install the systemd unit

```sh
sudo cp recvdata.service /etc/systemd/system/recvdata.service
```

### 4. Enable and start

```sh
sudo systemctl daemon-reload
sudo systemctl enable recvdata.service
sudo systemctl start recvdata.service
```

- Status: `sudo systemctl status recvdata.service`
- Logs: `journalctl -u recvdata.service` (messages are also written to syslog)

## Config file details (config.ini)

| Section | Key | Description |
| :-- | :-- | :-- |
| `[uecs]` | Port | UDP port to receive on (normally 16520). Also Version, Room, Region, Order, NodeName |
| `[mqtt]` | Valid | Enabled only when `yes` |
| | TopicTop, BrokerHost, Port, User, Passwd, Id | MQTT broker connection and topic settings |
| `[uecsrelay]` | Valid | Enabled only when `yes` |
| | host | Destination host (destination port is fixed to 16520) |
| `[uecsconsole]` | Valid | Enabled for **anything other than `no`** |
| | url | URL to POST to |
| | User, Passwd | Basic auth credentials (required when enabled; startup fails without them) |
| | Workers | Number of POST workers (default 4) |
| `[m304*]` | id, ip, mac | Device table for UECS Console. Every section whose name starts with `m304` is read; messages from `ip` are posted for `mac` (upper-cased) |

- The `[mqtt]`, `[uecsrelay]` and `[uecsconsole]` sections must **exist even when disabled**, because `Valid` is read from each.
- `[uecsconsole]` `Valid` is evaluated the opposite way from the others: to disable it you must write `Valid = no`.

## File summary

| File | Purpose |
| :-- | :-- |
| recvdata.py | Main UECS message receiver/forwarder |
| config.ini | Operation and forwarding settings (`/usr/local/etc/uecsgw/`) |
| config.ini-sample | Template for config.ini |
| recvdata.service | systemd service unit file |
| recvdata-rotation.sh | Example log rotation script (needs a separate `uecsrxd-insert.py`) |
