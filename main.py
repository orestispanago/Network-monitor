import sqlite3
import subprocess
import xml.etree.ElementTree as ET
import csv
from datetime import datetime
import ipaddress
from dataclasses import dataclass
from ftplib import FTP
import logging
import logging.config
import os
import traceback
from devices import DEVICE_MAP

dname = os.path.dirname(__file__)
os.chdir(dname)

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)

DB_NAME = "network.db"
CSV_NAME = "network.csv"
IP_RANGE = ""
FTP_IP = ""
FTP_USER = ""
FTP_PASSWORD = ""
FTP_DIR = "/dataloggers/network-monitor"


@dataclass
class Host:
    ip: str
    mac: str
    vendor: str
    last_seen: str
    description: str


def create_ip_list():
    prefix, r = IP_RANGE.rsplit(".", 1)
    start, end = map(int, r.split("-"))
    return [f"{prefix}.{i}" for i in range(start, end + 1)]


def setup_db(ip_list):
    """Initializes the DB and pre-populates IPs if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    curr = conn.cursor()
    curr.execute(
        """
        CREATE TABLE IF NOT EXISTS hosts (
            ip TEXT PRIMARY KEY,
            mac TEXT,
            vendor TEXT,
            last_seen DATETIME,
            description TEXT
        )
        """
    )
    for ip in ip_list:
        curr.execute("INSERT OR IGNORE INTO hosts (ip) VALUES (?)", (ip,))
    conn.commit()
    conn.close()


def run_nmap_scan():
    logger.debug("Running nmap...")
    cmd = ["sudo", "nmap", "-sn", IP_RANGE, "-oX", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    logger.debug("Nmap finished")
    return result.stdout


def parse_nmap_xml(xml_data):
    logger.debug("Parsing nmap xml output")
    scan_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z %Z")
    root = ET.fromstring(xml_data)
    hosts = []
    for host in root.findall("host"):
        status = host.find("status")
        if status is not None and status.get("state") == "up":
            for addr in host.findall("address"):
                addr_type = addr.get("addrtype")
                if addr_type == "ipv4":
                    ip = addr.get("addr")
                elif addr_type == "mac":
                    mac = addr.get("addr")
                    vendor = addr.get("vendor", "Unknown")
        description = DEVICE_MAP.get(mac, "Unknown Device")
        host = Host(
            ip=ip,
            mac=mac,
            vendor=vendor,
            last_seen=scan_time,
            description=description,
        )
        hosts.append(host)
    logger.debug(f"Found {len(hosts)} hosts")
    return hosts


def update_db(hosts_list):
    conn = sqlite3.connect(DB_NAME)
    curr = conn.cursor()
    for host in hosts_list:
        curr.execute(
            """
            UPDATE hosts 
            SET mac = ?, vendor = ?, last_seen = ? , description = ?
            WHERE ip = ?
            """,
            (host.mac, host.vendor, host.last_seen, host.description, host.ip),
        )
    conn.commit()
    conn.close()


def db_to_csv():
    logger.debug(f"Exporting 'hosts' table from {DB_NAME} to {CSV_NAME}")
    conn = sqlite3.connect(DB_NAME)
    curr = conn.cursor()
    curr.execute("SELECT * FROM hosts ORDER BY ip")
    rows = curr.fetchall()
    sorted_rows = sorted(rows, key=lambda x: ipaddress.IPv4Address(x[0]))
    headers = [description[0] for description in curr.description]
    conn.close()

    with open(CSV_NAME, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(sorted_rows)
    logger.debug(f"Exported {len(rows)} rows to {CSV_NAME}")


def upload_csv():
    with FTP(FTP_IP, FTP_USER, FTP_PASSWORD) as ftp_session:
        ftp_session.cwd(FTP_DIR)
        remote_path = f"{FTP_DIR}/{CSV_NAME}"
        with open(CSV_NAME, "rb") as f:
            ftp_session.storbinary(f"STOR {remote_path}", f)
    logger.debug(f"Uploaded {CSV_NAME} to {remote_path}")


def main():
    logger.info(f"{'-' * 15} START {'-' * 15}")
    ip_list = create_ip_list()
    setup_db(ip_list)
    xml_output = run_nmap_scan()
    hosts = parse_nmap_xml(xml_output)
    update_db(hosts)
    db_to_csv()
    upload_csv()
    logger.info(f"{'-' * 15} SUCCESS {'-' * 15}")


if __name__ == "__main__":
    try:
        main()
    except:
        logger.error("uncaught exception: %s", traceback.format_exc())
