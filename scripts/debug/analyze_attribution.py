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

print("=" * 80)
print("ÚLTIMA RNC - ANÁLISE DE ATRIBUIÇÃO")
print("=" * 80)
print(f"RNC ID: {rnc[0]}")
print(f"RNC Número: {rnc[1]}")
print(f"causador_user_id: {rnc[2]} ({'PREENCHIDO' if rnc[2] else 'VAZIO'})")
print(f"assigned_group_id: {rnc[3]}")
print(f"created_at: {rnc[4]}")

# Buscar nome do causador
if rnc[2]:
    cursor.execute('SELECT name FROM users WHERE id = ?', (rnc[2],))
    causador = cursor.fetchone()
    print(f"Nome do Causador: {causador[0] if causador else 'N/A'}")
else:
    print("Nome do Causador: (VAZIO - deveria ir para todo o grupo)")

# Compartilhamentos
cursor.execute("""
    SELECT shared_with_user_id, permission_level 
    FROM rnc_shares 
    WHERE rnc_id = ?
    ORDER BY shared_with_user_id
""", (rnc[0],))
shares = cursor.fetchall()

print(f"\n{'=' * 80}")
print(f"COMPARTILHADA COM {len(shares)} USUÁRIOS:")
print("=" * 80)

user_ids = []
for share in shares:
    cursor.execute('SELECT name FROM users WHERE id = ?', (share[0],))
    user = cursor.fetchone()
    user_ids.append(share[0])
    print(f"  - ID {share[0]:3d}: {user[0] if user else '?':30s} [{share[1]}]")

# Buscar todos os usuários do grupo para comparar
if rnc[3]:
    cursor.execute("""
        SELECT id, name FROM users WHERE group_id = ? ORDER BY name
    """, (rnc[3],))
    all_group_users = cursor.fetchall()
    
    print(f"\n{'=' * 80}")
    print(f"TODOS OS USUÁRIOS DO GRUPO {rnc[3]}:")
    print("=" * 80)
    for user in all_group_users:
        status = "✓ INCLUÍDO" if user[0] in user_ids else "✗ NÃO INCLUÍDO"
        print(f"  - ID {user[0]:3d}: {user[1]:30s} {status}")
    
    # Verificar gerentes do grupo
    cursor.execute("""
        SELECT manager_user_id, sub_manager_user_id 
        FROM groups 
        WHERE id = ?
    """, (rnc[3],))
    managers = cursor.fetchone()
    if managers:
        print(f"\n{'=' * 80}")
        print(f"GERENTES DO GRUPO {rnc[3]}:")
        print("=" * 80)
        if managers[0]:
            cursor.execute('SELECT name FROM users WHERE id = ?', (managers[0],))
            mgr = cursor.fetchone()
            status = "✓ INCLUÍDO" if managers[0] in user_ids else "✗ NÃO INCLUÍDO"
            print(f"  Gerente Principal: {mgr[0] if mgr else '?'} (ID: {managers[0]}) {status}")
        if managers[1]:
            cursor.execute('SELECT name FROM users WHERE id = ?', (managers[1],))
            sub = cursor.fetchone()
            status = "✓ INCLUÍDO" if managers[1] in user_ids else "✗ NÃO INCLUÍDO"
            print(f"  Sub-Gerente: {sub[0] if sub else '?'} (ID: {managers[1]}) {status}")
        
        # Verificar se Ronaldo está incluído
        print(f"\n{'=' * 80}")
        print("RONALDO (Valorista):")
        print("=" * 80)
        ronaldo_status = "✓ INCLUÍDO" if 11 in user_ids else "✗ NÃO INCLUÍDO"
        print(f"  Ronaldo (ID: 11) {ronaldo_status}")

# ANÁLISE
print(f"\n{'=' * 80}")
print("ANÁLISE:")
print("=" * 80)

if rnc[2]:
    expected_count = 4  # causador + gerente + sub-gerente + ronaldo
    print(f"✓ Causador PREENCHIDO → Deveria ir para {expected_count} pessoas")
    print(f"  (Causador + Gerente + Sub-Gerente + Ronaldo)")
    if len(shares) == expected_count:
        print(f"  ✓ CORRETO: {len(shares)} pessoas")
    else:
        print(f"  ✗ ERRO: Foi para {len(shares)} pessoas ao invés de {expected_count}")
else:
    print(f"✓ Causador VAZIO → Deveria ir para TODO O GRUPO")
    if len(shares) == len(all_group_users):
        print(f"  ✓ CORRETO: {len(shares)} pessoas")
    else:
        print(f"  ✗ ERRO: Foi para {len(shares)} pessoas ao invés de {len(all_group_users)}")

conn.close()
