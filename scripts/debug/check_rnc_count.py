import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM rncs WHERE is_deleted = 0')
print(f'Total RNCs ativas: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM rncs WHERE is_deleted = 0 AND status != "Finalizado"')
print(f'RNCs não finalizadas: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM rncs WHERE is_deleted = 0 AND status = "Finalizado"')
print(f'RNCs finalizadas: {cursor.fetchone()[0]}')

cursor.execute('SELECT status, COUNT(*) FROM rncs WHERE is_deleted = 0 GROUP BY status')
print('\nRNCs por status:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

conn.close()
