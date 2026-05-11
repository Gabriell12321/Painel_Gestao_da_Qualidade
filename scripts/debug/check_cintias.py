import sqlite3

conn = sqlite3.connect("ippel_system.db")
cursor = conn.cursor()

# Buscar todas as RNCs com "Cintia"
cursor.execute("""
    SELECT id, responsavel, area_responsavel, setor, status, created_at
    FROM rncs 
    WHERE is_deleted = 0 
    AND (responsavel LIKE "%Cintia%" OR responsavel LIKE "%Cíntia%")
    ORDER BY responsavel, created_at DESC
    LIMIT 20
""")

print("=== RNCs COM CINTIA ===\n")
cintia_simples = []
cintia_gracas = []

for row in cursor.fetchall():
    resp = row[1]
    if "Graças" in resp or "Gracas" in resp or "Kosiba" in resp:
        cintia_gracas.append(row)
    else:
        cintia_simples.append(row)

print(f"CINTIA DAS GRAÇAS KOSIBA (ENGENHARIA - CORRETA): {len(cintia_gracas)} RNCs")
for row in cintia_gracas[:5]:
    print(f"  ID {row[0]}: resp=\"{row[1]}\", area={row[2]}, data={row[5][:10]}")

print(f"\nCINTIA (COMPRAS - PARA REMOVER): {len(cintia_simples)} RNCs")
for row in cintia_simples[:5]:
    print(f"  ID {row[0]}: resp=\"{row[1]}\", area={row[2]}, data={row[5][:10]}")

# Contar totais
cursor.execute("SELECT COUNT(*) FROM rncs WHERE is_deleted = 0 AND responsavel = \"Cintia\"")
total_simples = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM rncs WHERE is_deleted = 0 AND responsavel LIKE \"%Cintia das Gra%\"")
total_gracas = cursor.fetchone()[0]

print(f"\nTOTAL:")
print(f"  Cintia (simples): {total_simples} RNCs")
print(f"  Cintia das Graças: {total_gracas} RNCs")

conn.close()
