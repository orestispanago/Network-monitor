import csv
import io
from datetime import datetime, timezone
from functools import wraps

import db
from flask import (
    Flask,
    Response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from config import SECRET_KEY, USERS

app = Flask(__name__)
app.secret_key = SECRET_KEY


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in USERS and check_password_hash(
            USERS.get(username), password
        ):
            session["user"] = username
            return redirect(url_for("index"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/add/<mac_address>", methods=["GET", "POST"])
@login_required
def add_device(mac_address):
    if request.method == "POST":
        db.add_known_device(
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
@login_required
def delete_device(mac_address):
    db.delete_known_device(mac_address)
    return redirect(url_for("index"))


@app.route("/edit/<mac_address>", methods=["GET", "POST"])
@login_required
def edit_device(mac_address):
    if request.method == "POST":
        db.update_known_device(
            mac_address=mac_address,
            administrator=request.form.get("administrator"),
            device_type=request.form.get("device_type"),
            hostname=request.form.get("hostname"),
            description=request.form.get("description"),
            floor=request.form.get("floor"),
            ethernet_port=request.form.get("ethernet_port"),
        )
        return redirect(url_for("index"))
    device = db.get_known_device(mac_address)
    return render_template(
        "edit_device.html", device=device, mac_address=mac_address
    )


@app.route("/")
@login_required
def index():
    devices = db.get_network_map()
    scan_time = db.get_scan_time()
    return render_template("home.html", devices=devices, scan_time=scan_time)


@app.route("/download")
@login_required
def download_csv():
    devices = db.get_network_map()
    headers = [k for k in devices[0].keys() if k != "is_known"]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in devices:
        writer.writerow([row[k] for k in headers])
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    filename = f"lab_subnet_{timestamp}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
