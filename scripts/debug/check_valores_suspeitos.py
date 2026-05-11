import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Ver valores específicos suspeitos
cursor.execute("""
SELECT rnc_number, price, created_at 
FROM rncs 
WHERE rnc_number IN ('34890', '34896', '34936')
ORDER BY rnc_number
""")

print('Valores armazenados no banco:')
for row in cursor.fetchall():
    print(f'RNC-{row[0]}: price = "{row[1]}" (tipo: {type(row[1])}) | Data: {row[2]}')

conn.close()
