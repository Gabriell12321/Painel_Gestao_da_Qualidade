import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Verificar as 3 últimas RNCs
cursor.execute("""
    SELECT id, rnc_number, causador_user_id, assigned_group_id
    FROM rncs 
    WHERE rnc_number IN ('34731', '34732', '34733')
    ORDER BY id
""")
rncs = cursor.fetchall()

print("=" * 100)
print("ANÁLISE DAS 3 RNCs VISÍVEIS NO DASHBOARD")
print("=" * 100)

for rnc in rncs:
    rnc_id = rnc[0]
    rnc_number = rnc[1]
    causador_id = rnc[2]
    group_id = rnc[3]
    
    print(f"\n{'=' * 100}")
    print(f"RNC {rnc_number} (ID: {rnc_id})")
    print("=" * 100)
    
    # Nome do causador
    if causador_id:
        cursor.execute('SELECT name FROM users WHERE id = ?', (causador_id,))
        causador = cursor.fetchone()
        print(f"Causador: {causador[0] if causador else 'N/A'} (ID: {causador_id})")
    else:
        print(f"Causador: (VAZIO - para todo o grupo)")
    
    # Compartilhamentos
    cursor.execute("""
        SELECT shared_with_user_id, permission_level
        FROM rnc_shares
        WHERE rnc_id = ?
        ORDER BY shared_with_user_id
    """, (rnc_id,))
    shares = cursor.fetchall()
    
    print(f"\nCompartilhada com {len(shares)} usuários:")
    for share in shares:
        cursor.execute('SELECT name FROM users WHERE id = ?', (share[0],))
        user = cursor.fetchone()
        print(f"  - {user[0] if user else '?'} (ID: {share[0]}) [{share[1]}]")
    
    # Verificar se todos do grupo foram incluídos
    if group_id:
        cursor.execute('SELECT COUNT(*) FROM users WHERE group_id = ?', (group_id,))
        total_group = cursor.fetchone()[0]
        
        if len(shares) == total_group:
            print(f"\n⚠️ ALERTA: Foi para TODOS os {total_group} usuários do grupo!")
        elif len(shares) == 4 and causador_id:
            print(f"\n✓ CORRETO: Apenas causador + gerentes + Ronaldo (4 pessoas)")

print(f"\n{'=' * 100}")
print("RECOMENDAÇÃO:")
print("=" * 100)
print("Abra o console do navegador (F12) e verifique:")
print("1. Em qual usuário você está logado")
print("2. Se você está vendo RNCs de outros usuários")
print("3. Se o cache do dashboard está desatualizado")

conn.close()
