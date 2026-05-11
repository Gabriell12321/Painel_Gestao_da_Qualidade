import sqlite3

conn = sqlite3.connect('database/ippel_system.db')
c = conn.cursor()

print("\n=== VERIFICANDO RESPONSAVEIS INVALIDOS ===\n")

c.execute("""
    SELECT id, numero, responsavel, area_responsavel, creator_department, status
    FROM rnc 
    WHERE responsavel IN ('lalinka', '14321') 
       OR responsavel LIKE '%lalinka%' 
       OR responsavel LIKE '%14321%'
    ORDER BY id DESC
    LIMIT 30
""")

rows = c.fetchall()
print(f"Total RNCs com lalinka/14321: {len(rows)}\n")

for r in rows:
    print(f"ID: {r[0]:5d} | RNC: {r[1]:10s} | Responsavel: {r[2]:20s} | Area: {r[3]:20s} | Dept: {r[4]:20s} | Status: {r[5]}")

print("\n=== VERIFICANDO DUPLICACAO ENGENHARIA ===\n")

c.execute("""
    SELECT DISTINCT creator_department, area_responsavel
    FROM rnc 
    WHERE creator_department LIKE '%ngenharia%' 
       OR area_responsavel LIKE '%ngenharia%'
    ORDER BY creator_department, area_responsavel
""")

rows = c.fetchall()
print(f"Total combinacoes Engenharia: {len(rows)}\n")

for r in rows:
    dept = r[0] if r[0] else 'NULL'
    area = r[1] if r[1] else 'NULL'
    print(f"Dept: {dept:30s} | Area: {area}")

print("\n=== CONTAGEM POR VARIACAO ===\n")

c.execute("""
    SELECT creator_department, COUNT(*) as total
    FROM rnc 
    WHERE creator_department LIKE '%ngenharia%'
    GROUP BY creator_department
    ORDER BY total DESC
""")

rows = c.fetchall()
for r in rows:
    print(f"{r[0]:30s} : {r[1]:5d} RNCs")

conn.close()
