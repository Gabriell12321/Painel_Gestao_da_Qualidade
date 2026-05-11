#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar permissões da Cintia e do grupo Engenharia
"""

import sqlite3
import sys
import os

# Adicionar o diretório services ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_PATH = 'ippel_system.db'

def check_permissions():
    print("=" * 80)
    print("VERIFICAÇÃO DE PERMISSÕES - CINTIA E ENGENHARIA")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Buscar Cintia
    cursor.execute('''
        SELECT u.id, u.name, u.email, u.department, u.role, u.group_id, u.permissions,
               g.name as group_name, g.manager_user_id, g.sub_manager_user_id
        FROM users u
        LEFT JOIN groups g ON u.group_id = g.id
        WHERE u.name LIKE '%Cintia%' OR u.name LIKE '%Cíntia%'
    ''')
    
    cintia = cursor.fetchone()
    
    if not cintia:
        print("❌ Cintia não encontrada no banco de dados")
        conn.close()
        return
    
    user_id, name, email, dept, role, group_id, perms_json, group_name, manager_id, sub_manager_id = cintia
    
    print(f"\n👤 USUÁRIO: {name}")
    print(f"   ID: {user_id}")
    print(f"   Email: {email}")
    print(f"   Departamento: {dept}")
    print(f"   Role: {role}")
    print(f"   Grupo ID: {group_id}")
    print(f"   Grupo Nome: {group_name}")
    
    # Verificar se é gerente ou sub-gerente
    is_manager = (user_id == manager_id)
    is_sub_manager = (user_id == sub_manager_id)
    
    print(f"\n👔 CARGO NO GRUPO:")
    print(f"   É Gerente? {'✅ SIM' if is_manager else '❌ NÃO'}")
    print(f"   É Sub-Gerente? {'✅ SIM' if is_sub_manager else '❌ NÃO'}")
    
    # Verificar permissões individuais
    import json
    try:
        user_perms = json.loads(perms_json) if perms_json else []
    except:
        user_perms = []
    
    print(f"\n🔐 PERMISSÕES INDIVIDUAIS:")
    if user_perms:
        for perm in user_perms:
            print(f"   - {perm}")
    else:
        print("   (Nenhuma permissão individual)")
    
    has_reply_rncs = 'reply_rncs' in user_perms
    has_admin = role == 'admin' or 'admin_access' in user_perms
    
    print(f"\n✅ PERMISSÕES CRÍTICAS:")
    print(f"   reply_rncs: {'✅ SIM' if has_reply_rncs else '❌ NÃO'}")
    print(f"   admin_access: {'✅ SIM' if has_admin else '❌ NÃO'}")
    
    # Verificar permissões do grupo
    if group_id:
        cursor.execute('''
            SELECT permission_name, permission_value
            FROM group_permissions
            WHERE group_id = ?
        ''', (group_id,))
        
        group_perms = cursor.fetchall()
        
        print(f"\n🔐 PERMISSÕES DO GRUPO '{group_name}':")
        if group_perms:
            for perm_name, perm_value in group_perms:
                status = '✅ ATIVADA' if perm_value else '❌ DESATIVADA'
                print(f"   - {perm_name}: {status}")
                
            # Verificar reply_rncs no grupo
            group_has_reply = any(p[0] == 'reply_rncs' and p[1] for p in group_perms)
            print(f"\n   reply_rncs no grupo: {'✅ SIM' if group_has_reply else '❌ NÃO'}")
        else:
            print("   (Nenhuma permissão configurada para este grupo)")
    
    # Verificar Alan (Admin) para comparação
    print(f"\n{'=' * 80}")
    print("COMPARAÇÃO COM ALAN (ADMIN)")
    print(f"{'=' * 80}")
    
    cursor.execute('''
        SELECT u.id, u.name, u.role, u.permissions, g.name as group_name
        FROM users u
        LEFT JOIN groups g ON u.group_id = g.id
        WHERE u.name LIKE '%Alan%'
    ''')
    
    alan = cursor.fetchone()
    
    if alan:
        alan_id, alan_name, alan_role, alan_perms_json, alan_group = alan
        
        try:
            alan_perms = json.loads(alan_perms_json) if alan_perms_json else []
        except:
            alan_perms = []
        
        print(f"\n👤 USUÁRIO: {alan_name}")
        print(f"   ID: {alan_id}")
        print(f"   Role: {alan_role}")
        print(f"   Grupo: {alan_group}")
        
        print(f"\n🔐 PERMISSÕES:")
        if alan_perms:
            for perm in alan_perms:
                print(f"   - {perm}")
        
        alan_has_reply = 'reply_rncs' in alan_perms
        alan_is_admin = alan_role == 'admin'
        
        print(f"\n✅ PERMISSÕES CRÍTICAS:")
        print(f"   reply_rncs: {'✅ SIM' if alan_has_reply else '❌ NÃO'}")
        print(f"   É admin: {'✅ SIM' if alan_is_admin else '❌ NÃO'}")
    
    print(f"\n{'=' * 80}")
    print("DIAGNÓSTICO")
    print(f"{'=' * 80}")
    
    if not has_reply_rncs and not has_admin:
        print("\n❌ PROBLEMA IDENTIFICADO:")
        print(f"   {name} NÃO tem a permissão 'reply_rncs'")
        print(f"   {name} NÃO é admin")
        print(f"\n💡 SOLUÇÃO:")
        print(f"   1. Adicionar permissão 'reply_rncs' para {name}")
        print(f"   2. OU adicionar 'reply_rncs' para o grupo '{group_name}'")
        print(f"   3. OU tornar {name} gerente/sub-gerente (já é: {is_sub_manager})")
        
        # Verificar se já é gerente/sub-gerente
        if is_manager or is_sub_manager:
            print(f"\n⚠️ ATENÇÃO:")
            print(f"   {name} é {'gerente' if is_manager else 'sub-gerente'} do grupo")
            print(f"   MAS ainda precisa da permissão 'reply_rncs' para editar RNCs")
    else:
        print(f"\n✅ {name} TEM permissões adequadas para editar RNCs")
    
    conn.close()

if __name__ == '__main__':
    check_permissions()
