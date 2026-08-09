import os
from werkzeug.security import generate_password_hash

USERS = {"admin": generate_password_hash("labsecret123")}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "network.db")
