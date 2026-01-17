from sqlite_to_csv import export_db_to_csv
from nmap_to_sqlite import update_database

update_database("net.xml", "hosts.db")
export_db_to_csv("hosts.db", "hosts", "hosts.csv")
