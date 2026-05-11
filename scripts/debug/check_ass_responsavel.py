import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Verificar se a coluna existe
cursor.execute("PRAGMA table_info(rncs)")
columns = cursor.fetchall()
print("=== Colunas relacionadas a 'responsavel' ===")
for col in columns:
    if 'responsavel' in col[1].lower() or 'ass_' in col[1].lower():
        print(f"  - {col[1]} ({col[2]})")

print("\n=== Última RNC criada ===")
cursor.execute("""
    SELECT rnc_number, area_responsavel, ass_responsavel, created_at
    FROM rncs
    ORDER BY id DESC
    LIMIT 1
""")
last_rnc = cursor.fetchone()
if last_rnc:
    print(f"RNC: {last_rnc[0]}")
    print(f"area_responsavel: {last_rnc[1]}")
    print(f"ass_responsavel: '{last_rnc[2]}'")
    print(f"created_at: {last_rnc[3]}")
else:
    print("Nenhuma RNC encontrada")

conn.close()
