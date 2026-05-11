import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

print('=== VERIFICANDO VALORES DE NOVEMBRO ===\n')

# Top 10 valores
cursor.execute("""
SELECT r.rnc_number, COALESCE(u.name, r.responsavel) as resp, r.price
FROM rncs r
LEFT JOIN users u ON CAST(r.responsavel AS TEXT) = CAST(u.id AS TEXT)
WHERE r.is_deleted = 0 
AND strftime('%Y-%m', r.created_at) = '2025-11'
AND r.price IS NOT NULL
AND r.price != ''
AND r.price != '0'
ORDER BY CAST(REPLACE(REPLACE(REPLACE(r.price, 'R$', ''), ',', ''), ' ', '') AS REAL) DESC
LIMIT 15
""")

print('Top 15 RNCs com maior valor:')
print('RNC | Responsável | Valor')
print('-' * 80)
total_top = 0
for row in cursor.fetchall():
    try:
        val = float(str(row[2]).replace('R$', '').replace(',', '').replace(' ', ''))
        total_top += val
        print(f'{row[0]} | {row[1]} | {row[2]} -> R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
    except:
        print(f'{row[0]} | {row[1]} | {row[2]} -> ERRO')

print(f'\nSoma dos top 15: R$ {total_top:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

# Verificar formato dos valores
print('\n=== FORMATO DOS VALORES NO BANCO ===')
cursor.execute("""
SELECT DISTINCT price
FROM rncs
WHERE is_deleted = 0 
AND strftime('%Y-%m', created_at) = '2025-11'
AND price IS NOT NULL
AND price != ''
AND price != '0'
LIMIT 20
""")
print('Exemplos de formatos:')
for row in cursor.fetchall():
    print(f'  "{row[0]}"')

conn.close()
