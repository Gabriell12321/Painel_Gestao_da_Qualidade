import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Última RNC criada
cursor.execute("""
    SELECT id, rnc_number, causador_user_id, assigned_group_id, created_at 
    FROM rncs 
    ORDER BY id DESC 
    LIMIT 1
""")
rnc = cursor.fetchone()

print("=" * 60)
print("ÚLTIMA RNC CRIADA")
print("=" * 60)
print(f"RNC ID: {rnc[0]}")
print(f"RNC Número: {rnc[1]}")
print(f"causador_user_id: {rnc[2]}")
print(f"assigned_group_id: {rnc[3]}")
print(f"created_at: {rnc[4]}")

# Buscar nome do causador
if rnc[2]:
    cursor.execute('SELECT name FROM users WHERE id = ?', (rnc[2],))
    causador = cursor.fetchone()
    print(f"Nome do Causador: {causador[0] if causador else 'N/A'}")
else:
    print("Nome do Causador: (vazio)")

# Compartilhamentos
cursor.execute("""
    SELECT shared_with_user_id, permission_level 
    FROM rnc_shares 
    WHERE rnc_id = ?
""", (rnc[0],))
shares = cursor.fetchall()

print(f"\n{'=' * 60}")
print(f"COMPARTILHADA COM {len(shares)} USUÁRIOS:")
print("=" * 60)
for share in shares:
    cursor.execute('SELECT name FROM users WHERE id = ?', (share[0],))
    user = cursor.fetchone()
    print(f"  - ID {share[0]:3d}: {user[0] if user else '?':30s} [{share[1]}]")

# Verificar gerentes do grupo
if rnc[3]:
    cursor.execute("""
        SELECT manager_user_id, sub_manager_user_id 
        FROM groups 
        WHERE id = ?
    """, (rnc[3],))
    managers = cursor.fetchone()
    if managers:
        print(f"\n{'=' * 60}")
        print(f"GERENTES DO GRUPO {rnc[3]}:")
        print("=" * 60)
        if managers[0]:
            cursor.execute('SELECT name FROM users WHERE id = ?', (managers[0],))
            mgr = cursor.fetchone()
            print(f"  Gerente Principal: {mgr[0] if mgr else '?'} (ID: {managers[0]})")
        if managers[1]:
            cursor.execute('SELECT name FROM users WHERE id = ?', (managers[1],))
            sub = cursor.fetchone()
            print(f"  Sub-Gerente: {sub[0] if sub else '?'} (ID: {managers[1]})")

conn.close()
