import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Buscar gerentes do grupo Engenharia
cursor.execute('''
    SELECT g.id, g.name, g.manager_user_id, g.sub_manager_user_id,
           m.name as manager_name, sm.name as sub_manager_name
    FROM groups g
    LEFT JOIN users m ON g.manager_user_id = m.id
    LEFT JOIN users sm ON g.sub_manager_user_id = sm.id
    WHERE g.id = 7
''')
grupo = cursor.fetchone()

print("=== GRUPO ENGENHARIA ===")
print(f"ID: {grupo[0]}")
print(f"Nome: {grupo[1]}")
print(f"Gerente Principal ID: {grupo[2]} -> {grupo[4]}")
print(f"Sub-gerente ID: {grupo[3]} -> {grupo[5]}")

# Buscar última RNC
cursor.execute('''
    SELECT id, rnc_number, causador_user_id, assigned_group_id
    FROM rncs
    ORDER BY id DESC
    LIMIT 1
''')
rnc = cursor.fetchone()

print(f"\n=== ÚLTIMA RNC (ID: {rnc[0]}) ===")
print(f"Número: {rnc[1]}")
print(f"causador_user_id: {rnc[2]}")
print(f"assigned_group_id: {rnc[3]}")

# Buscar quem é o causador
cursor.execute('SELECT name FROM users WHERE id = ?', (rnc[2],))
causador = cursor.fetchone()
print(f"Causador: {causador[0] if causador else 'N/A'}")

# Buscar compartilhamentos
cursor.execute('''
    SELECT rs.shared_with_user_id, u.name
    FROM rnc_shares rs
    JOIN users u ON rs.shared_with_user_id = u.id
    WHERE rs.rnc_id = ?
    ORDER BY u.name
''', (rnc[0],))
shares = cursor.fetchall()

print(f"\n=== COMPARTILHADA COM {len(shares)} USUÁRIOS ===")
for share in shares:
    marker = ""
    if share[0] == grupo[2]:  # Gerente principal
        marker = " [GERENTE PRINCIPAL]"
    elif share[0] == grupo[3]:  # Sub-gerente
        marker = " [SUB-GERENTE]"
    elif share[0] == rnc[2]:  # Causador
        marker = " [CAUSADOR]"
    else:
        marker = " [??? NÃO DEVERIA ESTAR AQUI]"
    
    print(f"  - {share[1]} (ID: {share[0]}){marker}")

print("\n=== ESPERADO ===")
print(f"  - {causador[0]} (ID: {rnc[2]}) [CAUSADOR]")
if grupo[4]:
    print(f"  - {grupo[4]} (ID: {grupo[2]}) [GERENTE PRINCIPAL]")
if grupo[5]:
    print(f"  - {grupo[5]} (ID: {grupo[3]}) [SUB-GERENTE]")

conn.close()
