import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

print("=== VERIFICAÇÃO RNC-34921 ===\n")

# Buscar RNC-34921
cursor.execute("""
    SELECT id, rnc_number, status, user_id, causador_user_id, 
           assigned_group_id, created_at 
    FROM rncs 
    WHERE rnc_number = 'RNC-34921'
""")
rnc = cursor.fetchone()

if rnc:
    print("✅ RNC-34921 ENCONTRADA:")
    print(f"  ID: {rnc[0]}")
    print(f"  Número: {rnc[1]}")
    print(f"  Status: {rnc[2]}")
    print(f"  Criador: {rnc[3]}")
    print(f"  Causador: {rnc[4]}")
    print(f"  Grupo: {rnc[5]}")
    print(f"  Data: {rnc[6]}")
else:
    print("❌ RNC-34921 NÃO ENCONTRADA")

# Última RNC no banco
print("\n=== ÚLTIMA RNC NO BANCO ===\n")
cursor.execute("""
    SELECT id, rnc_number, status, created_at 
    FROM rncs 
    ORDER BY id DESC 
    LIMIT 1
""")
last = cursor.fetchone()
print(f"ID: {last[0]}")
print(f"Número: {last[1]}")
print(f"Status: {last[2]}")
print(f"Data: {last[3]}")

# Contador total
cursor.execute('SELECT COUNT(*) FROM rncs')
total = cursor.fetchone()[0]
print(f"\n=== TOTAL: {total} RNCs ===")

# Verificar se RNC-34921 está entre as últimas 20
print("\n=== ÚLTIMAS 20 RNCs ===")
cursor.execute("""
    SELECT rnc_number, id 
    FROM rncs 
    ORDER BY id DESC 
    LIMIT 20
""")
for row in cursor.fetchall():
    marker = " ← RNC-34921" if row[0] == 'RNC-34921' else ""
    print(f"{row[0]} (ID: {row[1]}){marker}")

conn.close()
