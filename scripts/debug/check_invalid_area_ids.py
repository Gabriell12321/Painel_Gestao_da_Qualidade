import sqlite3

conn = sqlite3.connect("ippel_system.db")
cursor = conn.cursor()

print("=== RNCs COM area_responsavel INVÁLIDO ===")
cursor.execute("""
    SELECT r.id, r.area_responsavel, r.setor, r.responsavel, r.status
    FROM rncs r
    WHERE r.is_deleted = 0 
    AND r.area_responsavel IN ('13', '17', '19', '21', '22', '23', '26')
    ORDER BY r.area_responsavel, r.id
""")

rows = cursor.fetchall()
print(f"Total: {len(rows)} RNCs\n")

# Agrupar por area_responsavel
invalid_ids = {}
for row in rows:
    area_id = row[1]
    if area_id not in invalid_ids:
        invalid_ids[area_id] = []
    invalid_ids[area_id].append({
        'id': row[0],
        'setor': row[2],
        'responsavel': row[3],
        'status': row[4]
    })

for area_id, rncs in sorted(invalid_ids.items()):
    print(f"--- ID {area_id} ({len(rncs)} RNCs) ---")
    for rnc in rncs[:3]:
        setor = rnc['setor'] if rnc['setor'] else '❌ SEM SETOR'
        print(f"  RNC {rnc['id']}: setor={setor:30} resp={rnc['responsavel']}")
    if len(rncs) > 3:
        print(f"  ... +{len(rncs)-3} RNCs")
    print()

conn.close()
