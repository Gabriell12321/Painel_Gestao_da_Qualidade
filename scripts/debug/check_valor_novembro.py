import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Buscar RNCs de novembro 2025
query = """
    SELECT COUNT(*), 
           SUM(CASE 
               WHEN price IS NULL OR TRIM(price) = '' OR price = '0' THEN 0
               ELSE CAST(
                   REPLACE(
                       REPLACE(
                           REPLACE(
                               REPLACE(TRIM(price), 'R$', ''),
                               '.', ''
                           ),
                           ',', '.'
                       ),
                       '"', ''
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
"""

cursor.execute(query)
result = cursor.fetchone()
print(f'Total RNCs: {result[0]}')
valor_total = result[1] if result[1] else 0
print(f'Valor Total: R$ {valor_total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

# Ver amostra de preços
cursor.execute("""
    SELECT rnc_number, price, created_at
    FROM rncs 
    WHERE is_deleted = 0 
    AND CASE
        WHEN created_at LIKE '__/__/____' THEN 
            substr(created_at, 7, 4) || '-' || substr(created_at, 4, 2) || '-' || substr(created_at, 1, 2)
        ELSE 
            DATE(created_at)
    END BETWEEN '2025-11-01' AND '2025-11-24'
    ORDER BY CAST(REPLACE(REPLACE(REPLACE(REPLACE(price, 'R$', ''), '.', ''), ',', '.'), '"', '') AS REAL) DESC
    LIMIT 20
""")

print('\nTop 20 RNCs com maior valor:')
for row in cursor.fetchall():
    print(f'RNC-{row[0]}: {row[1]} | Data: {row[2]}')

conn.close()
