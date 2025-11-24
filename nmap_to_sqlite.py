import xml.etree.ElementTree as ET
import sqlite3

xml_file = "/home/orestis/net.xml"
db_file = "nmap_results.db"

tree = ET.parse(xml_file)
root = tree.getroot()

nmap_start = root.attrib.get("startstr")
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS hosts (
    ip TEXT,
    mac TEXT,
    vendor TEXT,
    nmap_start TEXT
)
''')

for host in root.findall("host"):
    ip = mac = vendor = None
    for addr in host.findall("address"):
        if addr.attrib["addrtype"] == "ipv4":
            ip = addr.attrib["addr"]
        elif addr.attrib["addrtype"] == "mac":
            mac = addr.attrib["addr"]
            vendor = addr.attrib.get("vendor")
    
    cursor.execute('''
        INSERT INTO hosts (ip, mac, vendor, nmap_start)
        VALUES (?, ?, ?, ?)
    ''', (ip, mac, vendor, nmap_start))

conn.commit()
conn.close()
