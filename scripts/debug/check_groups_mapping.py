import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

print("=== TABELA GROUPS ===")
cursor.execute("SELECT id, name FROM groups ORDER BY id")
for row in cursor.fetchall():
    print(f"ID {row[0]}: {row[1]}")

print("\n=== MAPEAMENTO NAS RNCs DE OUTUBRO ===")
cursor.execute("""
SELECT 
    r.rnc_number,
    r.responsavel,
    r.area_responsavel,
    r.setor,
    g1.name as area_name,
    g2.name as setor_name,
    COALESCE(g1.name, g2.name, r.area_responsavel, r.setor, 'Não informado') as final_department
FROM rncs r
LEFT JOIN groups g1 ON CAST(r.area_responsavel AS TEXT) = CAST(g1.id AS TEXT)
LEFT JOIN groups g2 ON CAST(r.setor AS TEXT) = CAST(g2.id AS TEXT)
WHERE r.is_deleted = 0 
AND strftime('%Y-%m', r.created_at) = '2025-10'
AND r.responsavel IS NOT NULL
AND r.responsavel != ''
ORDER BY final_department, r.responsavel
LIMIT 30
""")

print("\nRNC | Responsavel | area_responsavel | setor | area_name | setor_name | final_department")
print("-" * 140)
for row in cursor.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}")

conn.close()
