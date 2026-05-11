import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Verificar tabela areas
print("=== TABELA AREAS ===")
cursor.execute("SELECT * FROM areas ORDER BY id")
areas = cursor.fetchall()
cursor.execute("PRAGMA table_info(areas)")
cols = [c[1] for c in cursor.fetchall()]
print(f"Colunas: {cols}")
for area in areas:
    print(area)

print("\n=== TABELA SECTORS ===")
cursor.execute("SELECT * FROM sectors ORDER BY id")
sectors = cursor.fetchall()
cursor.execute("PRAGMA table_info(sectors)")
cols = [c[1] for c in cursor.fetchall()]
print(f"Colunas: {cols}")
for sector in sectors:
    print(sector)

conn.close()
