# haproxy-galera
This project is inspired by [matthanley/haproxy-galera](https://github.com/matthanley/haproxy-galera), originally written in Bash.
This repository provides a Python 3 implementation of a health check TCP server for [HAProxy](http://www.haproxy.org/) to monitor MariaDB Galera Cluster nodes.
Unlike the original Bash-based script, this version uses Python 3 sockets and `mysql` command-line client to determine the state of the local Galera node and return an appropriate HTTP status to HAProxy.

## Installation

### Step 1: Copy Script

```bash
sudo cp main.py /usr/local/sbin/haproxy-galera
sudo chmod +x /usr/local/sbin/haproxy-galera
```

### Step 2: Install Dependencies

```bash
sudo apt update
sudo apt install python3-mysqldb python3-requests
```

---

### Dependencies

Requires `python3-mysqldb`, and `python3-requests` installed.

### Systemd

1. Copy the systemd service file:

```bash
sudo cp haproxy-galera.service /etc/systemd/system/
```

2. Enable and start the service:

```bash
sudo systemctl daemon-reexec
sudo systemctl enable haproxy-galera
sudo systemctl start haproxy-galera
```

The script will listen on port `9200`.

## Usage

### MariaDB Setup

Create a local user to connect and check status:

```mysql
CREATE USER 'haproxy_check'@'%';
GRANT USAGE ON *.* TO 'haproxy_check'@'%';
```

## ⚙️ HAProxy Configuration

```
backend mysql_backend
    mode tcp
    option httpchk
    balance leastconn
    default-server port 9200 inter 3s rise 3 fall 1 maxconn 128 maxqueue 128 weight 100 slowstart 30s
    server db1 192.168.153.121:3306 check
    server db2 192.168.153.122:3306 check
    server db3 192.168.153.123:3306 check backup
```
