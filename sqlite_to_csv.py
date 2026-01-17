import csv
import sqlite3


def select_db_table(db_file, table_name):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    column_names = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return column_names, rows


def table_to_csv(column_names, rows, output_csv):
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(column_names)
        writer.writerows(rows)


def export_db_to_csv(db_file, table_name, output_csv):
    column_names, rows = select_db_table(db_file, table_name)
    table_to_csv(column_names, rows, output_csv)
