import sqlite3

conn = sqlite3.connect('database/ippel_system.db')
cursor = conn.cursor()

cursor.execute('SELECT id, ro_number, title, client, status, finalized_at, created_at FROM ros ORDER BY id DESC LIMIT 5')
rows = cursor.fetchall()

print('R.O cadastrados:')
print(f'Total: {len(rows)}')
for r in rows:
    print(f'  ID: {r[0]} | R.O: {r[1]} | Título: {r[2]} | Cliente: {r[3]} | Status: {r[4]} | Finalizado: {r[5]} | Criado: {r[6]}')

conn.close()
