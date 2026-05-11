import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Verificar estrutura da tabela rncs
cursor.execute("PRAGMA table_info(rncs)")
columns = cursor.fetchall()
print("=== ESTRUTURA DA TABELA RNCS ===")
for col in columns:
    print(f"{col[1]} ({col[2]})")

print("\n=== SAMPLE DATA ===")
cursor.execute("""
    SELECT id, responsavel, area_responsavel, setor, user_id, assigned_user_id
    FROM rncs 
    WHERE is_deleted = 0 
    AND status IN ('Finalizado', 'Pendente')
    LIMIT 5
""")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}")
    print(f"  responsavel: {row[1]}")
    print(f"  area_responsavel: {row[2]}")
    print(f"  setor: {row[3]}")
    print(f"  user_id: {row[4]}")
    print(f"  assigned_user_id: {row[5]}")
    print()

conn.close()
