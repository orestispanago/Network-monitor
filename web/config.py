import os

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def require_env(key):
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"{key} must be set in .env")
    return value


USERS = {
    "admin": generate_password_hash(require_env("ADMIN_PASSWORD")),
    "guest": generate_password_hash(require_env("GUEST_PASSWORD")),
}
DB_PATH = os.path.join(BASE_DIR, "network.db")
SECRET_KEY = require_env("SECRET_KEY")
