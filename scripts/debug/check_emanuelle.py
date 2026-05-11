import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

print("=== VERIFICANDO EMANUELLE ===\n")

# Buscar usuário Emanuelle
cursor.execute('SELECT id, name, email, department FROM users WHERE LOWER(name) LIKE "%emanuelle%"')
users = cursor.fetchall()
print("1. Usuário(s) Emanuelle encontrado(s):")
for u in users:
    print(f"   ID: {u[0]}, Nome: {u[1]}, Email: {u[2]}, Dept: {u[3]}")

if users:
    emanuelle_id = users[0][0]
    
    # Verificar em group_managers
    print("\n2. Registro na tabela group_managers:")
    cursor.execute('''
        SELECT gm.group_id, gm.user_id, gm.manager_type, g.name 
        FROM group_managers gm 
        JOIN groups g ON gm.group_id = g.id 
        WHERE gm.user_id = ?
    ''', (emanuelle_id,))
    managers = cursor.fetchall()
    if managers:
        for m in managers:
            print(f"   Grupo ID: {m[0]}, Nome: {m[3]}, Tipo: {m[2]}")
    else:
        print("   NENHUM registro encontrado!")
    
    # Verificar nas colunas antigas
    print("\n3. Registro nas colunas antigas (manager_user_id/sub_manager_user_id):")
    cursor.execute('''
        SELECT id, name, manager_user_id, sub_manager_user_id 
        FROM groups 
        WHERE manager_user_id = ? OR sub_manager_user_id = ?
    ''', (emanuelle_id, emanuelle_id))
    old_groups = cursor.fetchall()
    if old_groups:
        for g in old_groups:
            print(f"   Grupo ID: {g[0]}, Nome: {g[1]}, Manager: {g[2]}, Sub: {g[3]}")
    else:
        print("   NENHUM registro encontrado!")

# Buscar grupo Engenharia
print("\n4. Grupo Engenharia:")
cursor.execute('SELECT id, name, manager_user_id, sub_manager_user_id FROM groups WHERE LOWER(name) LIKE "%engenharia%"')
eng_group = cursor.fetchall()
for g in eng_group:
    print(f"   ID: {g[0]}, Nome: {g[1]}, Manager: {g[2]}, Sub: {g[3]}")
    
    # Buscar todos os gerentes deste grupo
    cursor.execute('SELECT user_id, manager_type FROM group_managers WHERE group_id = ?', (g[0],))
    all_managers = cursor.fetchall()
    if all_managers:
        print(f"   Gerentes na nova tabela:")
        for m in all_managers:
            cursor.execute('SELECT name FROM users WHERE id = ?', (m[0],))
            user_name = cursor.fetchone()
            print(f"     - {user_name[0] if user_name else 'Unknown'} (ID: {m[0]}, Tipo: {m[1]})")

# Buscar RNCs do grupo Engenharia
print("\n5. RNCs atribuídas ao grupo Engenharia:")
if eng_group:
    eng_id = eng_group[0][0]
    cursor.execute('SELECT id, rnc_number, title, status FROM rncs WHERE assigned_group_id = ? AND (is_deleted = 0 OR is_deleted IS NULL)', (eng_id,))
    rncs = cursor.fetchall()
    print(f"   Total: {len(rncs)} RNCs")
    for r in rncs[:5]:  # Mostrar apenas 5 primeiras
        print(f"     - RNC-{r[1]}: {r[2]} ({r[3]})")

conn.close()
print("\n=== FIM DA VERIFICAÇÃO ===")
