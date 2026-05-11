import sqlite3
conn = sqlite3.connect("ippel_system.db")
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM rncs WHERE is_deleted = 0 AND COALESCE(area_responsavel, setor, \"\") = \"Não Definidos\"")
print(f"Total RNCs com Não Definidos: {cursor.fetchone()[0]}")
cursor.execute("SELECT id, responsavel, area_responsavel FROM rncs WHERE is_deleted = 0 AND area_responsavel = \"Não Definidos\" LIMIT 5")
for row in cursor.fetchall():
    print(f"  ID {row[0]}: {row[1]} (area: {row[2]})")
conn.close()
