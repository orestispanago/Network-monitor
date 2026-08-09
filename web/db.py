import sqlite3
from config import DB_PATH


def get_scan_time():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    curr = conn.cursor()
    curr.execute("SELECT max(last_seen) FROM network_scans")
    scan_time = curr.fetchone()
    conn.close()
    return scan_time[0]


def get_network_map():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    curr = conn.cursor()
    curr.execute("""
    SELECT 
        network_scans.ip, 
        network_scans.mac_address, 
        (known_devices.mac_address IS NOT NULL) AS is_known,
        known_devices.administrator, 
        known_devices.device_type, 
        known_devices.hostname, 
        known_devices.description,
        known_devices.floor, 
        known_devices.ethernet_port,
        network_scans.last_seen
        FROM network_scans
    LEFT JOIN known_devices 
    ON network_scans.mac_address = known_devices.mac_address;""")
    rows = curr.fetchall()
    conn.close()
    return rows


def get_known_device(mac_address):
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    curr = conn.cursor()
    curr.execute(
        "SELECT * FROM known_devices WHERE mac_address = ?", (mac_address,)
    )
    device = curr.fetchone()
    conn.close()
    return device


def add_known_device(
    mac_address,
    administrator,
    device_type,
    hostname,
    description,
    floor,
    ethernet_port,
):
    conn = sqlite3.connect(DB_PATH)
    curr = conn.cursor()
    curr.execute(
        """
        INSERT INTO known_devices (
            mac_address, administrator, device_type, hostname, description, floor, ethernet_port
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            mac_address,
            administrator,
            device_type,
            hostname,
            description,
            floor,
            ethernet_port,
        ),
    )
    conn.commit()
    conn.close()


def update_known_device(
    mac_address,
    administrator,
    device_type,
    hostname,
    description,
    floor,
    ethernet_port,
):
    conn = sqlite3.connect(DB_PATH)
    curr = conn.cursor()
    curr.execute(
        """
        UPDATE known_devices
        SET administrator = ?,
            device_type = ?,
            hostname = ?,
            description = ?,
            floor = ?,
            ethernet_port = ?
        WHERE mac_address = ?
        """,
        (
            administrator,
            device_type,
            hostname,
            description,
            floor,
            ethernet_port,
            mac_address,
        ),
    )
    conn.commit()
    conn.close()


def delete_known_device(mac_address):
    conn = sqlite3.connect(DB_PATH)
    curr = conn.cursor()
    curr.execute(
        "DELETE FROM known_devices WHERE mac_address = ?", (mac_address,)
    )
    conn.commit()
    conn.close()
