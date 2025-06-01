import sqlite3

conn = sqlite3.connect("parking_data.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM parking_log")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()