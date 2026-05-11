import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT rnc_number, ass_responsavel, area_responsavel, inspetor, causador_user_id
    FROM rncs 
    ORDER BY id DESC 
    LIMIT 1
""")
rnc = cursor.fetchone()

print("=" * 60)
print("ÚLTIMA RNC - CAMPOS DE CABEÇALHO")
print("=" * 60)
print(f"RNC: {rnc[0]}")
print(f"ass_responsavel: '{rnc[1]}'")
print(f"area_responsavel: '{rnc[2]}'")
print(f"inspetor: '{rnc[3]}'")
print(f"causador_user_id: {rnc[4]}")

# Buscar nome do causador
if rnc[4]:
    cursor.execute('SELECT name FROM users WHERE id = ?', (rnc[4],))
    causador = cursor.fetchone()
    print(f"Nome do Causador: {causador[0] if causador else 'N/A'}")

conn.close()
