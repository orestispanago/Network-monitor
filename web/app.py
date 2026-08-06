import os
import sqlite3
import ipaddress
from flask import Flask, render_template, request, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

USERS = {"admin": generate_password_hash("labsecret123")}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "network.db")


@auth.verify_password
def verify_password(username, password):
    if username in USERS and check_password_hash(USERS.get(username), password):
        return username


def get_network_scan_data(table="network_scans"):
    # URI mode opens the database in read-only mode to prevent locks with your scanner
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    curr = conn.cursor()
    curr.execute(f"SELECT * FROM {table} ORDER BY ip")
    rows = curr.fetchall()
    sorted_rows = sorted(rows, key=lambda x: ipaddress.IPv4Address(x[0]))
    headers = [description[0] for description in curr.description]
    conn.close()
    return sorted_rows


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


def delete_known_device(mac_address):
    conn = sqlite3.connect(DB_PATH)
    curr = conn.cursor()
    curr.execute(
        "DELETE FROM known_devices WHERE mac_address = ?", (mac_address,)
    )
    conn.commit()
    conn.close()


@app.route("/add/<mac_address>", methods=["GET", "POST"])
@auth.login_required
def add_device(mac_address):
    if request.method == "POST":
        add_known_device(
            mac_address=mac_address,
            administrator=request.form.get("administrator"),
            device_type=request.form.get("device_type"),
            hostname=request.form.get("hostname"),
            description=request.form.get("description"),
            floor=request.form.get("floor"),
            ethernet_port=request.form.get("ethernet_port"),
        )
        return redirect(url_for("index"))

    return render_template("add_device.html", mac_address=mac_address)


@app.route("/delete/<mac_address>", methods=["POST"])
@auth.login_required
def delete_device(mac_address):
    delete_known_device(mac_address)
    return redirect(url_for("index"))


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


@app.route("/edit/<mac_address>", methods=["GET", "POST"])
@auth.login_required
def edit_device(mac_address):
    if request.method == "POST":
        update_known_device(
            mac_address=mac_address,
            administrator=request.form.get("administrator"),
            device_type=request.form.get("device_type"),
            hostname=request.form.get("hostname"),
            description=request.form.get("description"),
            floor=request.form.get("floor"),
            ethernet_port=request.form.get("ethernet_port"),
        )
        return redirect(url_for("index"))

    device = get_known_device(mac_address)
    return render_template(
        "edit_device.html", device=device, mac_address=mac_address
    )


@app.route("/")
@auth.login_required
def index():
    devices = get_network_map()
    return render_template("index.html", devices=devices)


if __name__ == "__main__":
    # Listens on all local interfaces so you can access it from the university subnet
    app.run(host="0.0.0.0", port=5000, debug=False)
