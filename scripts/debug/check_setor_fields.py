import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT rnc_number, responsavel, setor, area_responsavel, ass_responsavel 
    FROM rncs 
    WHERE status="Finalizado" 
    LIMIT 10
''')

rows = cursor.fetchall()

print('\nRNC | Responsavel | Setor | Area_Resp | Ass_Resp')
print('-'*120)
for r in rows:
    print(f'{r[0]:8} | {(r[1] or "NULL"):20} | {(r[2] or "NULL"):20} | {(r[3] or "NULL"):20} | {(r[4] or "NULL"):20}')

conn.close()
