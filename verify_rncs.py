import sqlite3

conn = sqlite3.connect('ippel_system.db')
c = conn.cursor()

print('=== Verificacao completa de RNCs problematicas ===\n')

# 1. RNCs com numeros muito baixos
print('1. RNCs com numero < 33000:')
c.execute('SELECT id, rnc_number, created_at FROM rncs WHERE rnc_number GLOB "[0-9]*" AND CAST(rnc_number AS INTEGER) < 33000 ORDER BY id')
rows = c.fetchall()
print(f'   Encontradas: {len(rows)}')
for r in rows[:10]:
    print(f'   ID: {r[0]} | {r[1]} | {r[2]}')

# 2. RNCs com datas REALMENTE futuras (2026+)
print('\n2. RNCs com datas realmente futuras (2026+):')
c.execute("SELECT id, rnc_number, created_at, title FROM rncs WHERE created_at LIKE '2026%' OR created_at LIKE '2027%' OR created_at LIKE '203%'")
rows = c.fetchall()
print(f'   Encontradas: {len(rows)}')
for r in rows:
    title = (r[3] or '')[:40]
    print(f'   ID: {r[0]} | {r[1]} | {r[2]} | {title}')

# 3. RNCs com formato de numero estranho
print('\n3. RNCs com formato de numero estranho (nao numerico e nao RNC-):')
c.execute('SELECT id, rnc_number, created_at FROM rncs WHERE rnc_number NOT GLOB "[0-9]*" AND rnc_number NOT LIKE "RNC-%" LIMIT 20')
rows = c.fetchall()
print(f'   Encontradas: {len(rows)}')
for r in rows:
    print(f'   ID: {r[0]} | {r[1]} | {r[2]}')

# 4. RNCs duplicadas por numero
print('\n4. Numeros RNC duplicados:')
c.execute('SELECT rnc_number, COUNT(*) as cnt FROM rncs GROUP BY rnc_number HAVING cnt > 1 ORDER BY cnt DESC LIMIT 10')
rows = c.fetchall()
print(f'   Encontradas: {len(rows)} numeros duplicados')
for r in rows:
    print(f'   {r[0]}: {r[1]} ocorrencias')

# 5. RNCs com titulo vazio ou suspeito
print('\n5. RNCs com titulo vazio ou muito curto:')
c.execute('SELECT id, rnc_number, title FROM rncs WHERE title IS NULL OR LENGTH(title) < 3 LIMIT 10')
rows = c.fetchall()
print(f'   Encontradas: {len(rows)}')
for r in rows:
    print(f'   ID: {r[0]} | {r[1]} | titulo: "{r[2]}"')

# 6. Estatisticas
print('\n6. Estatisticas:')
c.execute('SELECT MIN(id), MAX(id), COUNT(*) FROM rncs')
r = c.fetchone()
print(f'   Min ID: {r[0]}, Max ID: {r[1]}, Total: {r[2]}')

print(f'\n=== Total de RNCs no banco: {r[2]} ===')

conn.close()
