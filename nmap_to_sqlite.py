import sqlite3
from xml_parser import get_xml_hosts

xml_file = "net.xml"
db_file = "nmap_results.db"

hosts = get_xml_hosts(xml_file)

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS hosts (
    ip TEXT,
    mac TEXT,
    vendor TEXT,
    last_seen TEXT
)
"""
)

for host in hosts:
    cursor.execute(
        """
        INSERT INTO hosts (ip, mac, vendor, last_seen)
        VALUES (?, ?, ?, ?)
    """,
        (host.ip_address, host.mac_address, host.vendor, host.last_seen),
    )

conn.commit()
conn.close()
