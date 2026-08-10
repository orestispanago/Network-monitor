import io
import logging
import logging.config
import os
import sqlite3
import traceback
from datetime import datetime, timezone
from ftplib import FTP

from config import DB_NAME, FTP_DIR, FTP_IP, FTP_PASSWORD, FTP_USER

dname = os.path.dirname(os.path.dirname(__file__))
os.chdir(dname)

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger("backup")


def upload_in_memory_backup():
    logger.info(f"{'-' * 15} START {'-' * 15}")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    remote_path = f"{FTP_DIR}/network_{timestamp}.db"
    with sqlite3.connect(DB_NAME) as conn:
        db_bytes = conn.serialize()
    with FTP(FTP_IP, FTP_USER, FTP_PASSWORD) as ftp:
        ftp.cwd(FTP_DIR)
        ftp.storbinary(f"STOR {remote_path}", io.BytesIO(db_bytes))
    logger.info(f"Uploaded {DB_NAME} contents to {remote_path}")
    logger.info(f"{'-' * 15} SUCCESS {'-' * 15}")


if __name__ == "__main__":
    try:
        upload_in_memory_backup()
    except:
        logger.error("uncaught exception: %s", traceback.format_exc())
