import os
import sqlite3
import ipaddress
from flask import Flask, render_template
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


def get_db_data():
    # URI mode opens the database in read-only mode to prevent locks with your scanner
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    curr = conn.cursor()
    curr.execute("SELECT * FROM hosts ORDER BY ip")
    rows = curr.fetchall()
    sorted_rows = sorted(rows, key=lambda x: ipaddress.IPv4Address(x[0]))
    headers = [description[0] for description in curr.description]
    conn.close()
    return sorted_rows


@app.route("/")
@auth.login_required
def index():
    devices = get_db_data()
    return render_template("index.html", devices=devices)


if __name__ == "__main__":
    # Listens on all local interfaces so you can access it from the university subnet
    app.run(host="0.0.0.0", port=5000, debug=False)
