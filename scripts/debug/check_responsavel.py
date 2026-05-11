import sqlite3

DB_PATH = r'y:\rnc hml\ippel_system.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("=== Buscar nome do responsável ID 61 ===")
c.execute('SELECT id, name FROM users WHERE id = 61')
row = c.fetchone()
if row:
    print(f"ID: {row[0]}")
    print(f"Nome: {row[1]}")
else:
    print("Usuário não encontrado")

print("\n=== Verificar campo responsavel das RNCs ===")
c.execute('''
    SELECT rnc_number, responsavel, created_at, price
    FROM rncs
    WHERE rnc_number IN ("32421", "34958")
''')

for row in c.fetchall():
    print(f"RNC-{row[0]}: responsavel='{row[1]}', data={row[2]}, price={row[3]}")

conn.close()
