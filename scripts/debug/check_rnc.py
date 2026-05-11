import sqlite3

conn = sqlite3.connect('ippel_system.db')
c = conn.cursor()

# Buscar RNC 34960
rows = c.execute("SELECT id, rnc_number, cause_rnc, price FROM rncs WHERE rnc_number = '34960' OR rnc_number = 'RNC-34960'").fetchall()

print(f"Found {len(rows)} rows")
for r in rows:
    print(f"\nID: {r[0]}")
    print(f"RNC: {r[1]}")
    print(f"Causa: {repr(r[2])}")
    print(f"Price: {repr(r[3])}")
    print(f"Price type: {type(r[3])}")

conn.close()
