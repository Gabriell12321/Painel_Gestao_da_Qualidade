import sqlite3

conn = sqlite3.connect('database/rnc_system.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("Tabelas no rnc_system.db:")
for table in tables:
    print(f"  - {table[0]}")

conn.close()
