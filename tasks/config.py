import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def require_env(key):
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"{key} must be set in .env")
    return value


DB_PATH = os.path.join(BASE_DIR, "network.db")
SCANS_TABLE = "network_scans"
IP_RANGE = require_env("IP_RANGE")
FTP_IP = require_env("FTP_IP")
FTP_USER = require_env("FTP_USER")
FTP_PASSWORD = require_env("FTP_PASSWORD")
FTP_DIR = "/dataloggers/network-monitor"
