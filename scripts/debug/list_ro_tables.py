import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ro%'")
tables = cursor.fetchall()

if tables:
    print("Tabelas R.O encontradas:")
    for table in tables:
        print(f"  - {table[0]}")
else:
    print("Nenhuma tabela R.O encontrada no banco")

conn.close()
