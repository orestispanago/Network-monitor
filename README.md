# Network-monitor

Parse `nmap` xml output and store to sqlite database to monitor local network.


Run `nmap` in a crontab to scan your local network in regular intervals.

Save the output in xml

`nmap` command:

``` bash
sudo nmap -v -sn 10.200.20.130-154 -oX net.xml
```

The `-v` flag includes down hosts.