import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

print("=== PROCURANDO 'engenharia' MINÚSCULO ===\n")

cursor.execute("""
SELECT DISTINCT area_responsavel 
FROM rncs 
WHERE is_deleted = 0 
AND strftime('%Y-%m', created_at) = '2025-10' 
AND LOWER(area_responsavel) = 'engenharia'
""")
print("No campo area_responsavel:")
for row in cursor.fetchall():
    print(f"  '{row[0]}'")

cursor.execute("""
SELECT DISTINCT setor 
FROM rncs 
WHERE is_deleted = 0 
AND strftime('%Y-%m', created_at) = '2025-10' 
AND LOWER(setor) = 'engenharia'
""")
print("\nNo campo setor:")
for row in cursor.fetchall():
    print(f"  '{row[0]}'")

# Verificar quais RNCs têm isso
cursor.execute("""
SELECT rnc_number, responsavel, area_responsavel, setor 
FROM rncs 
WHERE is_deleted = 0 
AND strftime('%Y-%m', created_at) = '2025-10'
AND (LOWER(area_responsavel) = 'engenharia' OR LOWER(setor) = 'engenharia')
AND (area_responsavel != '7' AND setor != '7')
""")

print("\n=== RNCs com 'engenharia' em texto ===")
print("RNC | Responsavel | area_responsavel | setor")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")

conn.close()
