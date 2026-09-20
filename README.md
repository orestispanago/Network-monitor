# Network-monitor

Scans a subnet on a schedule, stores discovered devices in a local SQLite
database, and serves a web dashboard to view, annotate and export them.

`scanner.py` script:

* Parses `nmap` XML output 

* stores host data in an SQLite database

`backup.py` script:

* Uploads database to FTP

`web/app.py`:

* Flask dashboard showing the scanned network (IP, MAC, vendor, last
  seen). Has add and edit capability for known devices (by mac address).

* Login-protected (`admin` can add/edit/delete known devices, `guest` is
  read-only), with CSV export of the current network map


`nmap` command example:

``` bash
sudo nmap -sn 10.200.20.130-154 -oX net.xml
```

## Requirements

* Python 3.11 or higher

* `pip install -r requirements.txt`

## Configuration

Copy your `.env` file in the project root (gitignored, never committed)

`nmap` permissions

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


## Cron jobs

Now the script can run from a regular crontab e.g. every 10 minutes

``` bash
# Scans local network
# Parse nmap xml output, store to .db (sqlite database)
*/10 * * * * ~/Network-monitor/.venv314/bin/python /home/lab/Network-monitor/tasks/scanner.py
```

For monthly backups to FTP:

``` bash
# Backup ~/Network-monitor/network.db to FTP every month
# At 00:00 on the first day of the month
0 0 1 * * ~/Network-monitor/.venv314/bin/python ~/Network-monitor/tasks/backup.py
```