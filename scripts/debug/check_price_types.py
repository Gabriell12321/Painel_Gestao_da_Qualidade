import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

cursor.execute("""
SELECT rnc_number, price, typeof(price)
FROM rncs 
WHERE strftime('%Y-%m', created_at) = '2025-11'
AND is_deleted = 0
AND status IN ('Finalizado', 'Pendente')
AND price IS NOT NULL
AND price != ''
AND price != '0'
ORDER BY typeof(price), rnc_number
""")

results = cursor.fetchall()
print(f'Total de RNCs com preço: {len(results)}\n')

text_prices = [r for r in results if r[2] == 'text']
real_prices = [r for r in results if r[2] == 'real']

print(f'TIPO TEXT: {len(text_prices)}')
for r in text_prices[:10]:
    print(f'  RNC {r[0]}: "{r[1]}"')

print(f'\nTIPO REAL: {len(real_prices)}')
for r in real_prices[:10]:
    print(f'  RNC {r[0]}: {r[1]}')

conn.close()
