import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Buscar top RNCs por valor
cursor.execute("""
SELECT rnc_number, price, client, equipment, description, status
FROM rncs 
WHERE is_deleted = 0 
AND CASE
    WHEN created_at LIKE '__/__/____' THEN 
        substr(created_at, 7, 4) || '-' || substr(created_at, 4, 2) || '-' || substr(created_at, 1, 2)
    ELSE 
        DATE(created_at)
END BETWEEN '2025-11-01' AND '2025-11-24'
AND price > 500
ORDER BY price DESC
LIMIT 10
""")

print('=== TOP 10 RNCs COM MAIOR VALOR (Novembro 2025) ===\n')
total_top10 = 0
for row in cursor.fetchall():
    price_raw = row[1]
    # Converter valor (pode ser float ou string)
    if isinstance(price_raw, (int, float)):
        valor = float(price_raw)
    else:
        # String brasileira
        price_clean = str(price_raw).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').replace('"', '').strip()
        valor = float(price_clean) if price_clean else 0
    
    total_top10 += valor
    print(f'RNC-{row[0]}: R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    print(f'  Cliente: {row[2]}')
    print(f'  Equipamento: {row[3]}')
    print(f'  Status: {row[5]}')
    print(f'  Descrição: {row[4][:150] if row[4] else "N/A"}...\n')

print(f'Total apenas TOP 10: R$ {total_top10:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

# Total geral
cursor.execute("""
SELECT COUNT(*), SUM(price)
FROM rncs 
WHERE is_deleted = 0 
AND CASE
    WHEN created_at LIKE '__/__/____' THEN 
        substr(created_at, 7, 4) || '-' || substr(created_at, 4, 2) || '-' || substr(created_at, 1, 2)
    ELSE 
        DATE(created_at)
END BETWEEN '2025-11-01' AND '2025-11-24'
AND price IS NOT NULL
AND price > 0
""")

result = cursor.fetchone()
print(f'\n=== TOTAL GERAL ===')
print(f'RNCs com valor: {result[0]}')
print(f'Valor total: R$ {result[1]:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

conn.close()
