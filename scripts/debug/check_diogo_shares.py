import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

diogo_id = 66

# Contar compartilhamentos
cursor.execute('SELECT COUNT(*) FROM rnc_shares WHERE shared_with_user_id = ?', (diogo_id,))
total_shares = cursor.fetchone()[0]

print(f"=== COMPARTILHAMENTOS DE DIOGO (ID: {diogo_id}) ===")
print(f"Total de compartilhamentos: {total_shares}\n")

# Buscar RNCs compartilhadas
cursor.execute("""
    SELECT rs.rnc_id, r.rnc_number, r.status, r.causador_user_id, 
           u.name as causador_name, r.assigned_group_id
    FROM rnc_shares rs
    JOIN rncs r ON rs.rnc_id = r.id
    LEFT JOIN users u ON r.causador_user_id = u.id
    WHERE rs.shared_with_user_id = ?
      AND r.is_deleted = 0
    ORDER BY r.created_at DESC
""", (diogo_id,))

shares = cursor.fetchall()

print(f"RNCs compartilhadas com Diogo:")
for share in shares:
    rnc_id, rnc_number, status, causador_id, causador_name, group_id = share
    print(f"  • RNC-{rnc_number} (status: {status})")
    print(f"    Causador: {causador_name} (ID: {causador_id})")
    print(f"    Grupo: {group_id}")
    print(f"    Diogo é causador? {'SIM' if causador_id == diogo_id else 'NÃO'}")
    print()

# Contar RNCs onde Diogo é causador
cursor.execute("""
    SELECT COUNT(*) FROM rncs 
    WHERE causador_user_id = ? 
      AND is_deleted = 0 
      AND status != 'Finalizado'
""", (diogo_id,))
causador_count = cursor.fetchone()[0]

print(f"\n=== RESUMO ===")
print(f"RNCs onde Diogo é causador (ativas): {causador_count}")
print(f"RNCs compartilhadas com Diogo: {len(shares)}")
print(f"RNCs compartilhadas INDEVIDAMENTE: {len([s for s in shares if s[3] != diogo_id])}")

conn.close()
