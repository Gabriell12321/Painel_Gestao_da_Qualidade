import sqlite3

conn = sqlite3.connect('database/ippel_system.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(ros)')
cols = cursor.fetchall()

print("Colunas da tabela ros:")
for col in cols:
    print(f"  {col[1]} ({col[2]})")

conn.close()
