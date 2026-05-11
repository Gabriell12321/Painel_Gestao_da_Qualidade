import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Buscar usuário Diogo
cursor.execute("""
    SELECT u.id, u.name, u.role, u.group_id, 
           g.name as group_name, g.manager_user_id, g.sub_manager_user_id
    FROM users u 
    LEFT JOIN groups g ON u.group_id = g.id 
    WHERE u.name LIKE '%diogo%'
""")

print("=== USUÁRIOS DIOGO ===")
for row in cursor.fetchall():
    user_id, name, role, group_id, group_name, manager_id, submanager_id = row
    print(f"\nID: {user_id}")
    print(f"Nome: {name}")
    print(f"Role: {role}")
    print(f"Group ID: {group_id}")
    print(f"Group Name: {group_name}")
    print(f"Manager ID: {manager_id}")
    print(f"Submanager ID: {submanager_id}")
    print(f"É gerente? {user_id == manager_id}")
    print(f"É subgerente? {user_id == submanager_id}")

# Buscar RNCs do grupo Engenharia
cursor.execute("""
    SELECT r.id, r.rnc_number, r.causador_user_id, r.assigned_group_id,
           u.name as causador_name
    FROM rncs r
    LEFT JOIN users u ON r.causador_user_id = u.id
    WHERE r.assigned_group_id = (SELECT id FROM groups WHERE name = 'Engenharia')
    AND r.is_deleted = 0
    AND r.status != 'Finalizado'
    LIMIT 10
""")

print("\n\n=== RNCs ENGENHARIA (primeiras 10) ===")
for row in cursor.fetchall():
    rnc_id, rnc_number, causador_id, group_id, causador_name = row
    print(f"RNC {rnc_number}: Causador={causador_name} (ID:{causador_id})")

conn.close()
