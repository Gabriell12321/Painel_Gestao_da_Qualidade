import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Buscar todas as RNCs de novembro com seus valores
query = """
    SELECT rnc_number, price, created_at
    FROM rncs 
    WHERE is_deleted = 0 
    AND CASE
        WHEN created_at LIKE '__/__/____' THEN 
            substr(created_at, 7, 4) || '-' || substr(created_at, 4, 2) || '-' || substr(created_at, 1, 2)
        ELSE 
            DATE(created_at)
    END BETWEEN '2025-11-01' AND '2025-11-24'
    AND price IS NOT NULL
    AND price != ''
    AND price != '0'
    ORDER BY rnc_number
"""

cursor.execute(query)
rows = cursor.fetchall()

print(f'Total de RNCs com valor: {len(rows)}\n')

total_somado = 0
print('Lista de valores:')
for row in rows:
    rnc_num = row[0]
    price_raw = row[1]
    
    # Converter preço
    try:
        price_clean = str(price_raw).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').replace('"', '').replace("'", '')
        price_float = float(price_clean) if price_clean else 0
    except:
        price_float = 0
    
    total_somado += price_float
    print(f'RNC-{rnc_num}: {price_raw} -> R$ {price_float:.2f}')

print(f'\n=== TOTAL SOMADO: R$ {total_somado:,.2f} ==='.replace(',', 'X').replace('.', ',').replace('X', '.'))

# Verificar se há valores muito altos suspeitos
print('\n=== Valores acima de R$ 500 ===')
cursor.execute("""
    SELECT rnc_number, price, client, equipment, description
    FROM rncs 
    WHERE is_deleted = 0 
    AND CASE
        WHEN created_at LIKE '__/__/____' THEN 
            substr(created_at, 7, 4) || '-' || substr(created_at, 4, 2) || '-' || substr(created_at, 1, 2)
        ELSE 
            DATE(created_at)
    END BETWEEN '2025-11-01' AND '2025-11-24'
    AND CAST(REPLACE(REPLACE(REPLACE(REPLACE(price, 'R$', ''), '.', ''), ',', '.'), '"', '') AS REAL) > 500
    ORDER BY CAST(REPLACE(REPLACE(REPLACE(REPLACE(price, 'R$', ''), '.', ''), ',', '.'), '"', '') AS REAL) DESC
""")

for row in cursor.fetchall():
    price_clean = str(row[1]).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.').replace('"', '')
    print(f'\nRNC-{row[0]}: {row[1]}')
    print(f'  Cliente: {row[2]}')
    print(f'  Equipamento: {row[3]}')
    print(f'  Descrição: {row[4][:100] if row[4] else "N/A"}...')

conn.close()
