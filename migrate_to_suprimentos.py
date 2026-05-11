import sqlite3
import os
import shutil
from datetime import datetime

# Caminho do banco
DB_PATH = 'ippel_system.db'

# Fazer backup primeiro
backup_name = f'ippel_system_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
print(f"=== BACKUP ===")
print(f"Criando backup: {backup_name}")
shutil.copy(DB_PATH, backup_name)
print(f"Backup criado com sucesso!")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("\n=== IDENTIFICANDO GRUPOS ===")

# Buscar IDs dos grupos
cursor.execute("SELECT id, name FROM groups WHERE name IN ('Compras', 'Terceiros', 'Suprimentos')")
grupos = cursor.fetchall()
for g in grupos:
    print(f"  Grupo: {g['name']} (ID: {g['id']})")

grupo_ids = {g['name']: g['id'] for g in grupos}

if 'Suprimentos' not in grupo_ids:
    print("\nERRO: Grupo 'Suprimentos' não existe! Criando...")
    cursor.execute("INSERT INTO groups (name) VALUES ('Suprimentos')")
    grupo_ids['Suprimentos'] = cursor.lastrowid
    print(f"  Grupo Suprimentos criado com ID: {grupo_ids['Suprimentos']}")

suprimentos_id = grupo_ids.get('Suprimentos')
compras_id = grupo_ids.get('Compras')
terceiros_id = grupo_ids.get('Terceiros')

print(f"\nIDs encontrados:")
print(f"  Suprimentos: {suprimentos_id}")
print(f"  Compras: {compras_id}")
print(f"  Terceiros: {terceiros_id}")

# === USUÁRIOS ===
print("\n=== USUÁRIOS A MIGRAR ===")

# Verificar estrutura da tabela users
cursor.execute("PRAGMA table_info(users)")
user_cols = [col[1] for col in cursor.fetchall()]
print(f"Colunas da tabela users: {user_cols}")

# Buscar usuários de Compras
if compras_id:
    cursor.execute("SELECT id, name, group_id FROM users WHERE group_id = ?", (compras_id,))
    users_compras = cursor.fetchall()
    print(f"\nUsuários em Compras ({len(users_compras)}):")
    for u in users_compras:
        print(f"  - {u['name']} (ID: {u['id']})")

# Buscar usuários de Terceiros
if terceiros_id:
    cursor.execute("SELECT id, name, group_id FROM users WHERE group_id = ?", (terceiros_id,))
    users_terceiros = cursor.fetchall()
    print(f"\nUsuários em Terceiros ({len(users_terceiros)}):")
    for u in users_terceiros:
        print(f"  - {u['name']} (ID: {u['id']})")

# === RNCs ===
print("\n=== RNCs A MIGRAR ===")

# Verificar colunas relacionadas a grupo na tabela rncs
cursor.execute("PRAGMA table_info(rncs)")
rnc_cols = [col[1] for col in cursor.fetchall()]
group_related_cols = [c for c in rnc_cols if 'group' in c.lower() or 'setor' in c.lower()]
print(f"Colunas de grupo em rncs: {group_related_cols}")

# RNCs do grupo Compras (por assigned_group_id)
if compras_id:
    cursor.execute("SELECT COUNT(*) as cnt FROM rncs WHERE assigned_group_id = ?", (compras_id,))
    cnt = cursor.fetchone()['cnt']
    print(f"\nRNCs com assigned_group_id = Compras: {cnt}")

# RNCs do grupo Terceiros
if terceiros_id:
    cursor.execute("SELECT COUNT(*) as cnt FROM rncs WHERE assigned_group_id = ?", (terceiros_id,))
    cnt = cursor.fetchone()['cnt']
    print(f"RNCs com assigned_group_id = Terceiros: {cnt}")

# RNCs por nome do setor
cursor.execute("SELECT COUNT(*) as cnt FROM rncs WHERE setor LIKE '%Compras%'")
cnt = cursor.fetchone()['cnt']
print(f"RNCs com setor LIKE 'Compras': {cnt}")

cursor.execute("SELECT COUNT(*) as cnt FROM rncs WHERE setor LIKE '%Terceiros%'")
cnt = cursor.fetchone()['cnt']
print(f"RNCs com setor LIKE 'Terceiros': {cnt}")

# === EXECUTAR MIGRAÇÃO ===
print("\n" + "="*50)
print("=== EXECUTANDO MIGRAÇÃO ===")
print("="*50)

# 1. Migrar usuários de Compras para Suprimentos
if compras_id and suprimentos_id:
    cursor.execute("UPDATE users SET group_id = ? WHERE group_id = ?", (suprimentos_id, compras_id))
    print(f"\n✅ Usuários de Compras migrados para Suprimentos: {cursor.rowcount}")

# 2. Migrar usuários de Terceiros para Suprimentos
if terceiros_id and suprimentos_id:
    cursor.execute("UPDATE users SET group_id = ? WHERE group_id = ?", (suprimentos_id, terceiros_id))
    print(f"✅ Usuários de Terceiros migrados para Suprimentos: {cursor.rowcount}")

# 3. Migrar RNCs por assigned_group_id
if compras_id and suprimentos_id:
    cursor.execute("UPDATE rncs SET assigned_group_id = ? WHERE assigned_group_id = ?", (suprimentos_id, compras_id))
    print(f"✅ RNCs (assigned_group_id) de Compras para Suprimentos: {cursor.rowcount}")

if terceiros_id and suprimentos_id:
    cursor.execute("UPDATE rncs SET assigned_group_id = ? WHERE assigned_group_id = ?", (suprimentos_id, terceiros_id))
    print(f"✅ RNCs (assigned_group_id) de Terceiros para Suprimentos: {cursor.rowcount}")

# 4. Migrar RNCs por nome do setor
cursor.execute("UPDATE rncs SET setor = 'Suprimentos' WHERE setor LIKE '%Compras%'")
print(f"✅ RNCs (setor) de Compras para Suprimentos: {cursor.rowcount}")

cursor.execute("UPDATE rncs SET setor = 'Suprimentos' WHERE setor LIKE '%Terceiros%'")
print(f"✅ RNCs (setor) de Terceiros para Suprimentos: {cursor.rowcount}")

# 5. Migrar gerentes (group_managers)
if compras_id and suprimentos_id:
    cursor.execute("UPDATE group_managers SET group_id = ? WHERE group_id = ?", (suprimentos_id, compras_id))
    print(f"✅ Gerentes de Compras para Suprimentos: {cursor.rowcount}")

if terceiros_id and suprimentos_id:
    cursor.execute("UPDATE group_managers SET group_id = ? WHERE group_id = ?", (suprimentos_id, terceiros_id))
    print(f"✅ Gerentes de Terceiros para Suprimentos: {cursor.rowcount}")

# 6. Atualizar permissões de grupo
if compras_id and suprimentos_id:
    cursor.execute("UPDATE group_permissions SET group_id = ? WHERE group_id = ?", (suprimentos_id, compras_id))
    print(f"✅ Permissões de Compras para Suprimentos: {cursor.rowcount}")

# Deletar permissões de Terceiros (evita conflito de constraint)
if terceiros_id:
    cursor.execute("DELETE FROM group_permissions WHERE group_id = ?", (terceiros_id,))
    print(f"✅ Permissões de Terceiros removidas: {cursor.rowcount}")

# Commit das mudanças
conn.commit()
print("\n✅ COMMIT realizado com sucesso!")

# === VERIFICAÇÃO FINAL ===
print("\n=== VERIFICAÇÃO FINAL ===")

cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE group_id = ?", (suprimentos_id,))
print(f"Usuários em Suprimentos agora: {cursor.fetchone()['cnt']}")

cursor.execute("SELECT COUNT(*) as cnt FROM rncs WHERE assigned_group_id = ?", (suprimentos_id,))
print(f"RNCs em Suprimentos (assigned_group_id): {cursor.fetchone()['cnt']}")

cursor.execute("SELECT COUNT(*) as cnt FROM rncs WHERE setor = 'Suprimentos'")
print(f"RNCs em Suprimentos (setor): {cursor.fetchone()['cnt']}")

# Verificar se ainda há usuários em Compras/Terceiros
if compras_id:
    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE group_id = ?", (compras_id,))
    print(f"Usuários restantes em Compras: {cursor.fetchone()['cnt']}")

if terceiros_id:
    cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE group_id = ?", (terceiros_id,))
    print(f"Usuários restantes em Terceiros: {cursor.fetchone()['cnt']}")

conn.close()
print("\n=== MIGRAÇÃO CONCLUÍDA ===")
print(f"Backup disponível em: {backup_name}")
