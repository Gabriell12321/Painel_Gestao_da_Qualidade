import sqlite3

conn = sqlite3.connect("ippel_system.db")
cursor = conn.cursor()

# Verificar estrutura
cursor.execute("PRAGMA table_info(rncs)")
columns = [col[1] for col in cursor.fetchall()]

print("=== CAMPOS RELACIONADOS A SETOR/AREA ===")
setor_fields = [c for c in columns if 'setor' in c.lower() or 'area' in c.lower()]
for field in setor_fields:
    print(f"  - {field}")

print("\n=== SAMPLE DE area_responsavel ===")
cursor.execute("""
    SELECT id, area_responsavel, setor, responsavel
    FROM rncs 
    WHERE is_deleted = 0 
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"ID {row[0]}: area_responsavel={row[1]}, setor={row[2]}, responsavel={row[3]}")

conn.close()
