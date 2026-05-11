import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Total e soma de outubro/2025
cursor.execute("""
SELECT COUNT(*) as total, 
       SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(price, 'R$', ''), ' ', ''), ',', ''), '"', ''), '''', '') AS REAL)) as soma 
FROM rncs 
WHERE is_deleted = 0 
AND strftime('%Y-%m', created_at) = '2025-10' 
AND responsavel IS NOT NULL 
AND responsavel != '' 
AND CAST(responsavel AS TEXT) NOT GLOB '[0-9]*'
""")
result = cursor.fetchone()
print(f'Total RNCs Out/2025: {result[0]}')
soma = result[1] if result[1] else 0
print(f'Soma total: R$ {soma:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

# Listar todos os responsáveis
cursor.execute("""
SELECT DISTINCT responsavel 
FROM rncs 
WHERE is_deleted = 0 
AND strftime('%Y-%m', created_at) = '2025-10' 
ORDER BY responsavel
""")
print('\nResponsáveis em Out/2025:')
for row in cursor.fetchall():
    print(f'  - {row[0]}')

# Agrupar por responsável com valores
cursor.execute("""
SELECT responsavel, 
       COUNT(*) as qtd,
       SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(price, 'R$', ''), ' ', ''), ',', ''), '"', ''), '''', '') AS REAL)) as valor
FROM rncs 
WHERE is_deleted = 0 
AND strftime('%Y-%m', created_at) = '2025-10' 
AND responsavel IS NOT NULL 
AND responsavel != '' 
GROUP BY responsavel
ORDER BY valor DESC
""")
print('\nRNCs por Responsável (com valor):')
for row in cursor.fetchall():
    val = row[2] if row[2] else 0
    print(f'  {row[0]}: {row[1]} RNCs - R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

conn.close()
