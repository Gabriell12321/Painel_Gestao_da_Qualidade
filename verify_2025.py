import sqlite3

conn = sqlite3.connect('ippel_system.db')
c = conn.cursor()

print('=' * 70)
print('VERIFICAÇÃO COMPLETA - ANO 2025')
print('=' * 70)

# 0. Formatos de data
print('\n0. Formatos de data no banco:')
c.execute('''
    SELECT 
        CASE 
            WHEN created_at LIKE '____-__-__%' THEN 'YYYY-MM-DD'
            WHEN created_at LIKE '__/__/____' THEN 'DD/MM/YYYY'
            ELSE 'OUTRO'
        END as fmt,
        COUNT(*)
    FROM rncs
    GROUP BY fmt
''')
for r in c.fetchall():
    print(f'   {r[0]}: {r[1]} RNCs')

# 1. Distribuição por mês
print('\n1. Distribuição de RNCs por mês em 2025:')
c.execute('''
    SELECT 
        CASE 
            WHEN created_at LIKE '2025-01%' OR created_at LIKE '__/01/2025' THEN '01-Jan'
            WHEN created_at LIKE '2025-02%' OR created_at LIKE '__/02/2025' THEN '02-Fev'
            WHEN created_at LIKE '2025-03%' OR created_at LIKE '__/03/2025' THEN '03-Mar'
            WHEN created_at LIKE '2025-04%' OR created_at LIKE '__/04/2025' THEN '04-Abr'
            WHEN created_at LIKE '2025-05%' OR created_at LIKE '__/05/2025' THEN '05-Mai'
            WHEN created_at LIKE '2025-06%' OR created_at LIKE '__/06/2025' THEN '06-Jun'
            WHEN created_at LIKE '2025-07%' OR created_at LIKE '__/07/2025' THEN '07-Jul'
            WHEN created_at LIKE '2025-08%' OR created_at LIKE '__/08/2025' THEN '08-Ago'
            WHEN created_at LIKE '2025-09%' OR created_at LIKE '__/09/2025' THEN '09-Set'
            WHEN created_at LIKE '2025-10%' OR created_at LIKE '__/10/2025' THEN '10-Out'
            WHEN created_at LIKE '2025-11%' OR created_at LIKE '__/11/2025' THEN '11-Nov'
            WHEN created_at LIKE '2025-12%' OR created_at LIKE '__/12/2025' THEN '12-Dez'
            ELSE 'Outro: ' || created_at
        END as mes,
        COUNT(*) as total
    FROM rncs
    GROUP BY mes
    ORDER BY mes
''')
for r in c.fetchall():
    print(f'   {r[0]}: {r[1]} RNCs')

# 2. Verificar RNCs com anos diferentes de 2025
print('\n2. RNCs com anos diferentes de 2025:')
c.execute('''
    SELECT id, rnc_number, created_at, title 
    FROM rncs 
    WHERE created_at NOT LIKE '2025%' 
      AND created_at NOT LIKE '__/__/2025'
      AND created_at NOT LIKE '__/__/2025 %'
''')
rows = c.fetchall()
print(f'   Encontradas: {len(rows)}')
for r in rows[:30]:
    title = (r[3] or '')[:30]
    print(f'   ID: {r[0]} | {r[1]} | {r[2]} | {title}')

# 3. Estatísticas
print('\n' + '=' * 70)
c.execute('SELECT COUNT(*) FROM rncs')
print(f'TOTAL DE RNCs NO BANCO: {c.fetchone()[0]}')
print('=' * 70)

conn.close()
