import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Listar todas as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=== TABELAS NO DATABASE ===")
for t in tables:
    print(f"  {t[0]}")

print("\n=== VALORES ÚNICOS DE area_responsavel ===")
cursor.execute("""
    SELECT DISTINCT area_responsavel, COUNT(*) as cnt
    FROM rncs 
    WHERE is_deleted = 0 AND area_responsavel IS NOT NULL
    GROUP BY area_responsavel
    ORDER BY cnt DESC
    LIMIT 30
""")
rows = cursor.fetchall()
for row in rows:
    print(f"{row[0]}: {row[1]} RNCs")

print("\n=== VALORES ÚNICOS DE setor ===")
cursor.execute("""
    SELECT DISTINCT setor, COUNT(*) as cnt
    FROM rncs 
    WHERE is_deleted = 0 AND setor IS NOT NULL AND setor != ''
    GROUP BY setor
    ORDER BY cnt DESC
    LIMIT 30
""")
rows = cursor.fetchall()
for row in rows:
    print(f"{row[0]}: {row[1]} RNCs")

conn.close()
