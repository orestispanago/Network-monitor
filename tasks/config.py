import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_PATH = os.path.join(BASE_DIR, "network.db")
SCANS_TABLE = "network_scans"
IP_RANGE = os.environ.get("IP_RANGE", "")
FTP_IP = os.environ.get("FTP_IP", "")
FTP_USER = os.environ.get("FTP_USER", "")
FTP_PASSWORD = os.environ.get("FTP_PASSWORD", "")
FTP_DIR = "/dataloggers/network-monitor"
