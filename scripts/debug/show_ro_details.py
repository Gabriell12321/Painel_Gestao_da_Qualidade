import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM ros')
columns = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()

if rows:
    print(f"Total R.O: {len(rows)}\n")
    for row in rows:
        print("=" * 60)
        for col, val in zip(columns, row):
            print(f"{col:30} : {val}")
else:
    print("Nenhum R.O encontrado")

conn.close()
