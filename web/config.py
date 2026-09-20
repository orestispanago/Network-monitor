import os

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

USERS = {
    "admin": generate_password_hash(os.environ.get("ADMIN_PASSWORD", "")),
    "guest": generate_password_hash(os.environ.get("GUEST_PASSWORD", "")),
}
DB_PATH = os.path.join(BASE_DIR, "network.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "")
