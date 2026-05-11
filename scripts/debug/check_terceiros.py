import sqlite3

conn = sqlite3.connect("ippel_system.db")
cursor = conn.cursor()

# Verificar quantas RNCs de Terceiros existem
cursor.execute("""
    SELECT COUNT(*) FROM rncs 
    WHERE is_deleted = 0 
    AND COALESCE(area_responsavel, setor, "") = "Terceiros"
""")
print(f"Total RNCs Terceiros no banco: {cursor.fetchone()[0]}")

# Ver alguns exemplos
cursor.execute("""
    SELECT id, responsavel, area_responsavel, setor, status, created_at
    FROM rncs 
    WHERE is_deleted = 0 
    AND COALESCE(area_responsavel, setor, "") = "Terceiros"
    ORDER BY created_at DESC
    LIMIT 10
""")

print("\nExemplos de RNCs Terceiros:")
for row in cursor.fetchall():
    print(f"ID {row[0]}: resp={row[1]}, area={row[2]}, setor={row[3]}, status={row[4]}, data={row[5][:10]}")

conn.close()
