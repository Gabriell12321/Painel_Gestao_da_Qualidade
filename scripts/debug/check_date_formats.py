import sqlite3

DB_PATH = r'y:\rnc hml\ippel_system.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Contar formatos
c.execute('SELECT COUNT(*) FROM rncs WHERE created_at LIKE "____-__-%"')
iso_count = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM rncs WHERE created_at LIKE "__/__/____"')
br_count = c.fetchone()[0]

c.execute('SELECT COUNT(*) FROM rncs WHERE created_at IS NOT NULL AND created_at != ""')
total = c.fetchone()[0]

print(f"RNCs com formato ISO (YYYY-MM-DD): {iso_count}")
print(f"RNCs com formato BR (DD/MM/YYYY): {br_count}")
print(f"Total de RNCs com data: {total}")
print(f"RNCs sem padrão: {total - iso_count - br_count}")

# Mostrar exemplos de cada formato
print("\n=== Exemplos formato ISO ===")
c.execute('SELECT rnc_number, created_at FROM rncs WHERE created_at LIKE "____-__-%" LIMIT 3')
for row in c.fetchall():
    print(f"  RNC-{row[0]}: {row[1]}")

print("\n=== Exemplos formato BR ===")
c.execute('SELECT rnc_number, created_at FROM rncs WHERE created_at LIKE "__/__/____" LIMIT 3')
for row in c.fetchall():
    print(f"  RNC-{row[0]}: {row[1]}")

conn.close()
