import sqlite3
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
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


def create_ip_list():
    prefix, r = IP_RANGE.rsplit(".", 1)
    start, end = map(int, r.split("-"))
    return [f"{prefix}.{i}" for i in range(start, end + 1)]


def setup_db_table(ip_list, table=SCANS_TABLE):
    """Initializes scans table in DB and populates IPs if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    curr = conn.cursor()
    curr.execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            ip TEXT PRIMARY KEY,
            mac TEXT,
            vendor TEXT,
            last_seen DATETIME
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


def parse_nmap_xml(xml_data):
    logger.debug("Parsing nmap xml output")
    scan_time = datetime.now(timezone.utc).isoformat()
    root = ET.fromstring(xml_data)
    hosts = []
    local_ip, local_mac = get_local_ip_mac()
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
                parsed_host = Host(
                    ip=ip,
                    mac=mac,
                    vendor=vendor,
                    last_seen=scan_time,
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
            last_seen = NULL
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
                SET mac_address = ?, vendor = ?, last_seen = ?
                WHERE ip = ?
                """,
                (
                    host.mac,
                    host.vendor,
                    host.last_seen,
                    host.ip,
                ),
            )
        conn.commit()


def upload_to_ftp(fname):
    with FTP(FTP_IP, FTP_USER, FTP_PASSWORD) as ftp_session:
        ftp_session.cwd(FTP_DIR)
        remote_path = f"{FTP_DIR}/{fname}"
        with open(fname, "rb") as f:
            ftp_session.storbinary(f"STOR {remote_path}", f)
    logger.debug(f"Uploaded {fname} to {remote_path}")


def main():
    logger.info(f"{'-' * 15} START {'-' * 15}")
    ip_list = create_ip_list()
    setup_db_table(ip_list)
    xml_output = run_nmap_scan()
    hosts = parse_nmap_xml(xml_output)
    update_db(hosts)
    upload_to_ftp(DB_NAME)
    logger.info(f"{'-' * 15} SUCCESS {'-' * 15}")


if __name__ == "__main__":
    try:
        main()
    except:
        logger.error("uncaught exception: %s", traceback.format_exc())
