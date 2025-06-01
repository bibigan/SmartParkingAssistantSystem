import sqlite3

conn = sqlite3.connect("parking_data.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        distance REAL,
        led_status TEXT
    )
""")

conn.commit()
conn.close()