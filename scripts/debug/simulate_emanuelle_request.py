import sqlite3

# Simular exatamente a query que o servidor executa para usuários sem view_all_rncs
conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

emanuelle_id = 80
tab = 'active'

print(f"=== SIMULANDO REQUISIÇÃO /api/rnc/list?tab={tab} PARA EMANUELLE (ID: {emanuelle_id}) ===\n")

# Query EXATA do servidor (linha 3587 do server_form.py)
cursor.execute('''
    SELECT DISTINCT
        r.id,
        r.rnc_number,
        r.title,
        r.equipment,
        r.client,
        r.priority,
        r.status,
        r.user_id,
        r.assigned_user_id,
        r.created_at,
        r.updated_at,
        r.finalized_at,
        u.name AS user_name,
        u.department AS user_department,
        au.name AS assigned_user_name
    FROM rncs r 
    LEFT JOIN users u ON r.user_id = u.id
    LEFT JOIN users au ON r.assigned_user_id = au.id
    LEFT JOIN rnc_shares rs ON rs.rnc_id = r.id
    WHERE (r.is_deleted = 0 OR r.is_deleted IS NULL) 
    AND r.status NOT IN ('Finalizado') 
    AND (
        r.user_id = ? 
        OR r.assigned_user_id = ? 
        OR rs.shared_with_user_id = ?
        OR (r.assigned_group_id IS NOT NULL AND EXISTS (
            SELECT 1 FROM group_managers gm
            WHERE gm.group_id = r.assigned_group_id 
            AND gm.user_id = ?
        ))
        OR (r.assigned_group_id IS NOT NULL AND EXISTS (
            SELECT 1 FROM groups g 
            WHERE g.id = r.assigned_group_id 
            AND (g.manager_user_id = ? OR g.sub_manager_user_id = ?)
        ))
    )
    ORDER BY r.id DESC
''', (emanuelle_id, emanuelle_id, emanuelle_id, emanuelle_id, emanuelle_id, emanuelle_id))

rncs = cursor.fetchall()

print(f"Total de RNCs encontradas: {len(rncs)}\n")

# Agrupar por motivo de acesso
creator_count = 0
assigned_count = 0
shared_count = 0
manager_new_count = 0
manager_old_count = 0

for rnc in rncs:
    rnc_id, rnc_number, title, equipment, client, priority, status, user_id, assigned_user_id = rnc[:9]
    
    reasons = []
    if user_id == emanuelle_id:
        creator_count += 1
        reasons.append("criador")
    if assigned_user_id == emanuelle_id:
        assigned_count += 1
        reasons.append("atribuído")
    
    # Verificar compartilhamento
    cursor.execute('SELECT 1 FROM rnc_shares WHERE rnc_id = ? AND shared_with_user_id = ?', (rnc_id, emanuelle_id))
    if cursor.fetchone():
        shared_count += 1
        reasons.append("compartilhado")
    
    # Verificar gerente (nova tabela)
    cursor.execute('''
        SELECT 1 FROM rncs r
        WHERE r.id = ? AND r.assigned_group_id IS NOT NULL AND EXISTS (
            SELECT 1 FROM group_managers gm
            WHERE gm.group_id = r.assigned_group_id AND gm.user_id = ?
        )
    ''', (rnc_id, emanuelle_id))
    if cursor.fetchone():
        manager_new_count += 1
        reasons.append("gerente(nova)")
    
    # Verificar gerente (colunas antigas)
    cursor.execute('''
        SELECT 1 FROM rncs r
        WHERE r.id = ? AND r.assigned_group_id IS NOT NULL AND EXISTS (
            SELECT 1 FROM groups g
            WHERE g.id = r.assigned_group_id AND (g.manager_user_id = ? OR g.sub_manager_user_id = ?)
        )
    ''', (rnc_id, emanuelle_id, emanuelle_id))
    if cursor.fetchone():
        manager_old_count += 1
        reasons.append("gerente(antiga)")

print("=== MOTIVOS DE ACESSO ===")
print(f"RNCs criadas por Emanuelle: {creator_count}")
print(f"RNCs atribuídas a Emanuelle: {assigned_count}")
print(f"RNCs compartilhadas: {shared_count}")
print(f"RNCs via gerente (nova tabela): {manager_new_count}")
print(f"RNCs via gerente (coluna antiga): {manager_old_count}")

print(f"\n=== PRIMEIRAS 10 RNCs ===")
for i, rnc in enumerate(rncs[:10], 1):
    print(f"{i}. RNC-{rnc[1]}: {rnc[2][:50]} ({rnc[6]})")

conn.close()
print("\n=== FIM DA SIMULAÇÃO ===")
