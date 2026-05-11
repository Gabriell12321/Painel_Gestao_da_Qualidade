import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Buscar tabelas com 'valor' no nome
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%valor%'")
tables = cursor.fetchall()

print('Tabelas com "valor":', tables)

# Ver estrutura da tabela valores_hora
if tables:
    cursor.execute("PRAGMA table_info(valores_hora)")
    cols = cursor.fetchall()
    print('\nEstrutura da tabela valores_hora:')
    for col in cols:
        print(f'  {col[1]} ({col[2]})')

# Ver dados existentes agrupados por setor
cursor.execute("SELECT DISTINCT setor FROM valores_hora ORDER BY setor")
setores = cursor.fetchall()
print(f'\nSetores existentes ({len(setores)}):')
for s in setores:
    print(f'  - {s[0]}')

conn.close()
