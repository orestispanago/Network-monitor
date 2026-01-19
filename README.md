# Network-monitor

Parse `nmap` xml output and store to sqlite database to monitor local network.

Exports db to csv and uploads to FTP

This script is intended to run in a **sudo crontab**, not a user crontab.

`nmap` command example:

``` bash
sudo nmap -sn 10.200.20.130-154 -oX net.xml
```