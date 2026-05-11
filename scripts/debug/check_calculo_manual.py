import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Buscar apenas RNCs CRIADAS em novembro 2025 (não importadas)
# RNCs com número >= 34800 são de 2025
cursor.execute("""
SELECT rnc_number, price, created_at, client
FROM rncs 
WHERE is_deleted = 0 
AND CAST(rnc_number AS INTEGER) >= 34800
AND CASE
    WHEN created_at LIKE '__/__/____' THEN 
        substr(created_at, 7, 4) || '-' || substr(created_at, 4, 2) || '-' || substr(created_at, 1, 2)
    ELSE 
        DATE(created_at)
END BETWEEN '2025-11-01' AND '2025-11-24'
ORDER BY rnc_number
""")

rows = cursor.fetchall()
print(f'Total de RNCs NOVAS (>= 34800) em Novembro 2025: {len(rows)}\n')

total = 0
for row in rows:
    price_raw = row[1]
    
    # Converter preço
    if isinstance(price_raw, (int, float)):
        valor = float(price_raw)
    elif price_raw:
        price_clean = str(price_raw).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').replace('"', '').strip()
        try:
            valor = float(price_clean) if price_clean and price_clean != '0' else 0
        except:
            valor = 0
    else:
        valor = 0
    
    total += valor
    if valor > 0:
        print(f'RNC-{row[0]}: R$ {valor:,.2f} - {row[3]}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

print(f'\n=== TOTAL RNCs NOVAS: R$ {total:,.2f} ==='.replace(',', 'X').replace('.', ',').replace('X', '.'))

# Agora ver TODAS (incluindo importadas)
cursor.execute("""
SELECT COUNT(*), 
       SUM(CASE 
           WHEN typeof(price) = 'real' OR typeof(price) = 'integer' THEN price
           WHEN price IS NULL OR TRIM(price) = '' OR price = '0' THEN 0
           ELSE CAST(
               REPLACE(
                   REPLACE(
                       REPLACE(TRIM(price), 'R$', ''),
                       '.', ''
                   ),
                   ',', '.'
               ) AS REAL
           )
       END) as total_value
FROM rncs 
WHERE is_deleted = 0 
AND CASE
    WHEN created_at LIKE '__/__/____' THEN 
        substr(created_at, 7, 4) || '-' || substr(created_at, 4, 2) || '-' || substr(created_at, 1, 2)
    ELSE 
        DATE(created_at)
END BETWEEN '2025-11-01' AND '2025-11-24'
""")

result = cursor.fetchone()
print(f'\n=== TOTAL TODAS (incluindo importadas): {result[0]} RNCs ===')
print(f'Valor Total: R$ {result[1]:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

conn.close()
