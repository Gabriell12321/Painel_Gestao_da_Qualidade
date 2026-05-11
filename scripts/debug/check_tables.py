import sqlite3

conn = sqlite3.connect('database/ippel_system.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tabelas no banco:")
for table in tables:
    print(f"  - {table[0]}")

conn.close()
