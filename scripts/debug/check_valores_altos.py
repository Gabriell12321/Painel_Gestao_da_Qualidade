import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Buscar RNCs com valor > 1000
cursor.execute("""
SELECT rnc_number, price, client
FROM rncs 
WHERE is_deleted = 0 
AND CASE
    WHEN created_at LIKE '__/__/____' THEN 
        substr(created_at, 7, 4) || '-' || substr(created_at, 4, 2) || '-' || substr(created_at, 1, 2)
    ELSE 
        DATE(created_at)
END BETWEEN '2025-11-01' AND '2025-11-24'
""")

print('Analisando valores dos preços...\n')
acima_1000 = []
total = 0

for row in cursor.fetchall():
    price_raw = row[1]
    if not price_raw or price_raw in ['0', '']:
        continue
    
    # Limpar e converter
    price_clean = str(price_raw).replace('R$', '').replace(' ', '').replace('"', '').replace("'", '').strip()
    
    # Contar separadores
    dots = price_clean.count('.')
    commas = price_clean.count(',')
    
    # Determinar formato
    if dots > 0 and commas > 0:
        # Formato BR: 1.234,56
        price_float = float(price_clean.replace('.', '').replace(',', '.'))
    elif commas > 0:
        # Apenas vírgula: 1234,56
        price_float = float(price_clean.replace(',', '.'))
    else:
        # Apenas ponto ou sem separador
        price_float = float(price_clean)
    
    total += price_float
    
    if price_float > 1000:
        acima_1000.append((row[0], price_raw, price_float, row[2]))

print('=== RNCs com valor ACIMA de R$ 1.000,00 ===\n')
for item in sorted(acima_1000, key=lambda x: x[2], reverse=True):
    print(f'RNC-{item[0]}: {item[1]} (convertido: R$ {item[2]:,.2f}) - Cliente: {item[3]}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

print(f'\n=== TOTAL: R$ {total:,.2f} ==='.replace(',', 'X').replace('.', ',').replace('X', '.'))
print(f'Quantidade com valor > R$ 1.000: {len(acima_1000)}')

conn.close()
