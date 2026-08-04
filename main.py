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

dname = os.path.dirname(__file__)
os.chdir(dname)

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)

DB_NAME = "network.db"
SCANS_TABLE = "network_scans"
DEVICES_TABLE = "known_devices"
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


def setup_db(ip_list, table=SCANS_TABLE):
    """Initializes the DB and pre-populates IPs if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    curr = conn.cursor()
    curr.execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            ip TEXT PRIMARY KEY,
            mac TEXT,
            vendor TEXT,
            last_seen DATETIME,
            description TEXT
        )
        """)
    for ip in ip_list:
        curr.execute(f"INSERT OR IGNORE INTO {table} (ip) VALUES (?)", (ip,))
    conn.commit()
    conn.close()


def get_local_ip_mac():
    cmd = ["ip", "route", "get", "1.1.1.1"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout.split()
    iface = output[output.index("dev") + 1]
    ip_addr = output[output.index("src") + 1]
    with open(f"/sys/class/net/{iface}/address", "r") as f:
        mac_addr = f.read().strip().upper()
    return ip_addr, mac_addr


def run_nmap_scan():
    logger.debug("Running nmap...")
    cmd = ["sudo", "nmap", "-sn", IP_RANGE, "-oX", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    logger.debug("Nmap finished")
    return result.stdout


def get_known_device_descriptions(table=DEVICES_TABLE) -> dict:
    """Fetches all known MAC address descriptions into a dictionary at once."""
    with sqlite3.connect(DB_NAME) as conn:
        curr = conn.cursor()
        curr.execute(f"SELECT mac_address, description FROM '{table}'")
        return {row[0]: row[1] for row in curr.fetchall()}


def parse_nmap_xml(xml_data):
    logger.debug("Parsing nmap xml output")
    scan_time = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z %Z")
    root = ET.fromstring(xml_data)
    hosts = []
    local_ip, local_mac = get_local_ip_mac()
    known_devices = get_known_device_descriptions()
    for host in root.findall("host"):
        status = host.find("status")
        if status is not None and status.get("state") == "up":
            ip, mac, vendor = None, None, "Unknown"
            for addr in host.findall("address"):
                addr_type = addr.get("addrtype")
                if addr_type == "ipv4":
                    ip = addr.get("addr")
                elif addr_type == "mac":
                    mac = addr.get("addr")
                    vendor = addr.get("vendor", "Unknown")
            if ip == local_ip:
                mac = local_mac
            if ip and mac:
                description = known_devices.get(mac, "Unknown Device")
                parsed_host = Host(
                    ip=ip,
                    mac=mac,
                    vendor=vendor,
                    last_seen=scan_time,
                    description=description,
                )
                hosts.append(parsed_host)
    logger.debug(f"Found {len(hosts)} hosts")
    return hosts


def clear_duplicate_macs(cursor, table=SCANS_TABLE):
    """Finds duplicate MACs and sets all but last occurence fields to NULL"""
    cursor.execute(
        f"""
        WITH RankedHosts AS (
            SELECT 
                ip,
                ROW_NUMBER() OVER (
                    PARTITION BY mac_address 
                    ORDER BY last_seen DESC, ip DESC
                ) as rn
            FROM {table}
            WHERE mac_address IS NOT NULL
        )
        UPDATE {table}
        SET 
            mac_address = NULL,
            vendor = NULL,
            last_seen = NULL,
            description = NULL
        WHERE ip IN (
            SELECT ip 
            FROM RankedHosts 
            WHERE rn > 1
        );
        """,
    )
    logger.debug("Cleared duplicate MAC addressses keeping most recent IP")


def update_db(hosts_list, table=SCANS_TABLE):
    with sqlite3.connect(DB_NAME) as conn:
        curr = conn.cursor()
        clear_duplicate_macs(curr)
        for host in hosts_list:
            curr.execute(
                f"""
                UPDATE {table} 
                SET mac_address = ?, vendor = ?, last_seen = ?, description = ?
                WHERE ip = ?
                """,
                (
                    host.mac,
                    host.vendor,
                    host.last_seen,
                    host.description,
                    host.ip,
                ),
            )
        conn.commit()


def db_table_to_csv(table=SCANS_TABLE):
    logger.debug(f"Exporting {table} table to {CSV_NAME}")
    conn = sqlite3.connect(DB_NAME)
    curr = conn.cursor()
    curr.execute(f"SELECT * FROM {table} ORDER BY ip")
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
    db_table_to_csv()
    upload_csv()
    logger.info(f"{'-' * 15} SUCCESS {'-' * 15}")


if __name__ == "__main__":
    try:
        main()
    except:
        logger.error("uncaught exception: %s", traceback.format_exc())
