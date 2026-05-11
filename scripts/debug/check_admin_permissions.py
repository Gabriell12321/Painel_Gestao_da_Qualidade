import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Verificar permissões do usuário Alan (admin)
cursor.execute('''
    SELECT u.name, u.email, g.name as grupo
    FROM users u
    LEFT JOIN groups g ON u.group_id = g.id
    WHERE u.email = 'admin@ippel.com.br'
''')

user = cursor.fetchone()
if user:
    print(f"✓ Usuário: {user[0]}")
    print(f"  Email: {user[1]}")
    print(f"  Grupo: {user[2]}")
    
    # Verificar permissões do grupo
    if user[2]:
        cursor.execute('''
            SELECT permission_name 
            FROM group_permissions gp
            JOIN groups g ON gp.group_id = g.id
            WHERE g.name = ?
        ''', (user[2],))
        
        perms = cursor.fetchall()
        print(f"\n📋 Permissões do grupo '{user[2]}':")
        for p in perms:
            print(f"  - {p[0]}")

conn.close()
