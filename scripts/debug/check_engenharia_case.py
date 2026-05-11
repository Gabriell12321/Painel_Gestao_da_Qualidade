import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

print("=== VERIFICANDO CASO 'engenharia' vs 'Engenharia' ===\n")

# Verificar se há 'engenharia' minúsculo
cursor.execute("""
SELECT 
    r.rnc_number,
    r.responsavel,
    r.area_responsavel,
    r.setor,
    COALESCE(g.name, r.area_responsavel, r.setor, 'Não informado') as final_dept
FROM rncs r
LEFT JOIN groups g ON (
    CAST(r.area_responsavel AS TEXT) = CAST(g.id AS TEXT) OR
    CAST(r.setor AS TEXT) = CAST(g.id AS TEXT)
)
WHERE r.is_deleted = 0 
AND strftime('%Y-%m', r.created_at) = '2025-10'
AND (r.area_responsavel = 'engenharia' OR r.setor = 'engenharia')
""")

print("RNCs com 'engenharia' (minúsculo):")
print("RNC | responsavel | area_responsavel | setor | final_dept")
print("-" * 100)
minusculo = cursor.fetchall()
for row in minusculo:
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
print(f"Total: {len(minusculo)}")

# Verificar se há 'Engenharia' maiúsculo (via ID 7)
cursor.execute("""
SELECT 
    r.rnc_number,
    r.responsavel,
    r.area_responsavel,
    r.setor,
    COALESCE(g.name, r.area_responsavel, r.setor, 'Não informado') as final_dept
FROM rncs r
LEFT JOIN groups g ON (
    CAST(r.area_responsavel AS TEXT) = CAST(g.id AS TEXT) OR
    CAST(r.setor AS TEXT) = CAST(g.id AS TEXT)
)
WHERE r.is_deleted = 0 
AND strftime('%Y-%m', r.created_at) = '2025-10'
AND (r.area_responsavel = '7' OR r.setor = '7' OR g.name = 'Engenharia')
""")

print("\n\nRNCs com 'Engenharia' (via ID 7):")
print("RNC | responsavel | area_responsavel | setor | final_dept")
print("-" * 100)
maiusculo = cursor.fetchall()
for row in maiusculo:
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
print(f"Total: {len(maiusculo)}")

conn.close()
