# recvdata.py README

Here is an English README for your recvdata.py program, including setup and systemd service instructions, based on the provided files.[^1][^2][^3]

***

## Overview

**recvdata.py** is a daemon program that receives UECS protocol messages broadcast via UDP and forwards them to system syslog, an MQTT broker, or by HTTP POST to a console server as specified in a config file. All transfer and operational details are controlled via `config.ini`.[^2][^1]

## Installation and Setup

### 1. Install the Program and Config Files

- Place `recvdata.py` at `/usr/local/bin/recvdata.py` and make it executable.
- Copy `config.ini-sample` to `/usr/local/etc/uecsgw/config.ini` and edit settings to match your environment.[^2]

```sh
sudo cp recvdata.py /usr/local/bin/recvdata.py
sudo chmod +x /usr/local/bin/recvdata.py
sudo mkdir -p /usr/local/etc/uecsgw/
sudo cp config.ini-sample /usr/local/etc/uecsgw/config.ini
```


### 2. Install Required Python Packages

```sh
pip install paho-mqtt requests
```

- `requests` is required for HTTP POST. `paho-mqtt` is required for MQTT features.


### 3. Register systemd Service

- Copy `recvdata.service` to `/etc/systemd/system/recvdata.service`.[^3]

```sh
sudo cp recvdata.service /etc/systemd/system/recvdata.service
```


### 4. Enable and Start the Service

```sh
sudo systemctl daemon-reload
sudo systemctl enable recvdata.service
sudo systemctl start recvdata.service
```

- To check service status:

```sh
sudo systemctl status recvdata.service
```

- To check logs:

```sh
journalctl -u recvdata.service
```


## Config File Details

- **[uecs]**: Basic UECS receiver settings (port, room, region, etc.).
- **[mqtt]**: MQTT broker settings (`Valid=yes` enables).
- **[uecsconsole]**: UECS console server settings (`Valid=yes` enables).
- **[m304]**: Per-device (IP/MAC/ID) mapping settings.[^2]

See `config.ini-sample` for further reference.

## File Summary

| File Name | Purpose |
| :-- | :-- |
| recvdata.py | Main UECS message receiver/forwarder |
| config.ini | Operation and forwarding configuration |
| recvdata.service | systemd service unit file |


***

With this setup, the daemon will automatically launch at system start and continuously receive and forward UECS messages according to your configuration.[^1][^3][^2]

<div style="text-align: center">⁂</div>

[^1]: recvdata.py

[^2]: config.ini-sample

[^3]: recvdata.service

