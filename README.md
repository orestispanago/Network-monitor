# Network-monitor

`scanner.py` script:

* Parses `nmap` XML output 

* stores host data in an SQLite database

`backup.py` script:

* Uploads db to FTP


`nmap` command example:

``` bash
sudo nmap -sn 10.200.20.130-154 -oX net.xml
```


## `nmap` permissions

Running `nmap` without `sudo` prevents it from resolving MAC address or vendor. 

To run `scanner.py` via a regular (non-root) user's crontab, 
grant your user permission to run `sudo nmap` without a password prompt,
adding `NOPASSWD` rule in `sudoers` file.

Create a separate config for nmap

``` bash
sudo visudo -f /etc/sudoers.d/lab-nmap
```

Add this line (replace `lab` with your username)
``` bash
lab ALL=(ALL) NOPASSWD: /usr/bin/nmap
```

Make sure `sudo nmap` is in the code (e.g., via subprocess), to use `NOPASSWD` rule.


## Crontab

Now the script can run from a regular crontab e.g. every 10 minutes

``` bash
*/10 * * * * python3 ~/Network-monitor/scanner.py
```

For monthly backups to FTP (At 00:00 on first day of the month)
``` bash
0 0 1 * * python3 ~/Network-monitor/backup.py
```