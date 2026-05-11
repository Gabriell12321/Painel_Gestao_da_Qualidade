import sqlite3
import json

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

emanuelle_id = 80

print("=== VERIFICANDO PERMISSÕES DA EMANUELLE ===\n")

# Buscar permissões do usuário
cursor.execute('SELECT permissions, role, department FROM users WHERE id = ?', (emanuelle_id,))
user = cursor.fetchone()
if user:
    print(f"1. Permissões do usuário:")
    print(f"   Role: {user[1]}")
    print(f"   Department: {user[2]}")
    try:
        perms = json.loads(user[0]) if user[0] else []
        print(f"   Permissions: {perms}")
    except:
        print(f"   Permissions (raw): {user[0]}")

# Verificar permissões do grupo
cursor.execute('''
    SELECT gp.permission_name, gp.permission_value
    FROM group_permissions gp
    JOIN users u ON u.group_id = gp.group_id
    WHERE u.id = ? AND gp.permission_value = 1
''', (emanuelle_id,))
group_perms = cursor.fetchall()
print(f"\n2. Permissões do grupo:")
if group_perms:
    for p in group_perms:
        print(f"   - {p[0]}")
else:
    print("   NENHUMA permissão de grupo encontrada")

# Verificar se há cache
print(f"\n3. Verificar sessão/cache (não armazenado no DB)")
print("   IMPORTANTE: Limpar cache do navegador e fazer logout/login novamente")

conn.close()
print("\n=== FIM DA VERIFICAÇÃO ===")
