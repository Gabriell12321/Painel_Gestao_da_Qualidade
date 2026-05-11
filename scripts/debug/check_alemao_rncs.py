import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

cursor.execute("""
SELECT rnc_number, title, responsavel, created_at, price 
FROM rncs 
WHERE (LOWER(responsavel) LIKE '%alemao%' OR LOWER(responsavel) LIKE '%alemão%')
AND is_deleted = 0
ORDER BY CAST(rnc_number AS INTEGER) DESC 
LIMIT 100
""")

results = cursor.fetchall()
print(f'\n=== Total de RNCs do Alemão: {len(results)} ===\n')

for r in results:
    titulo = r[1][:60] if r[1] else 'Sem título'
    responsavel = r[2] if r[2] else 'N/A'
    data = r[3] if r[3] else 'N/A'
    valor = r[4] if r[4] else 'R$ 0,00'
    print(f'RNC {r[0]:5} | {titulo:60} | {responsavel:20} | {data:10} | {valor}')

conn.close()
