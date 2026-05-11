import sqlite3

DB_PATH = r'y:\rnc hml\ippel_system.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('''
    SELECT id, rnc_number, created_at, updated_at, status
    FROM rncs 
    WHERE rnc_number = '34958'
''')

row = cursor.fetchone()

if row:
    print(f"RNC-34958 no banco:")
    print(f"ID: {row[0]}")
    print(f"RNC: {row[1]}")
    print(f"created_at: '{row[2]}'")
    print(f"created_at[:10]: '{row[2][:10]}'")
    print(f"updated_at: {row[3]}")
    print(f"status: {row[4]}")
else:
    print("RNC não encontrada")

conn.close()
