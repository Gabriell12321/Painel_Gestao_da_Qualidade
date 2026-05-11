import sqlite3

conn = sqlite3.connect("ippel_system.db")
cursor = conn.cursor()

print("=== IDs NUMÉRICOS EM area_responsavel ===")
cursor.execute("""
    SELECT DISTINCT r.area_responsavel, COUNT(*) as cnt,
           a.name as area_name
    FROM rncs r
    LEFT JOIN areas a ON (r.area_responsavel GLOB "[0-9]*" AND CAST(r.area_responsavel AS INTEGER) = a.id)
    WHERE r.is_deleted = 0 
    AND r.area_responsavel GLOB "[0-9]*"
    GROUP BY r.area_responsavel
    ORDER BY CAST(r.area_responsavel AS INTEGER)
""")

for row in cursor.fetchall():
    area_id = row[0]
    cnt = row[1]
    name = row[2] if row[2] else "❌ NÃO EXISTE"
    print(f"ID {area_id:3} -> {name:20} ({cnt} RNCs)")

print("\n=== TABELA AREAS (IDs válidos) ===")
cursor.execute("SELECT id, name FROM areas ORDER BY id")
for row in cursor.fetchall():
    print(f"ID {row[0]:2} = {row[1]}")

conn.close()
