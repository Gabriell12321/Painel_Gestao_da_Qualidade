#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para listar e corrigir erros de português nos nomes dos usuários
"""

import sqlite3

DB_PATH = 'ippel_system.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Listar todos os usuários
    print("📋 USUÁRIOS NO BANCO DE DADOS:")
    print("=" * 80)
    cursor.execute("""
        SELECT u.id, u.username, u.full_name, g.name as grupo 
        FROM users u 
        LEFT JOIN groups g ON u.group_id = g.id 
        ORDER BY u.full_name
    """)
    
    users_with_errors = []
    
    for user_id, username, full_name, group_name in cursor.fetchall():
        # Detectar caracteres problemáticos
        has_error = False
        if full_name and ('�' in full_name or 'Ã' in full_name):
            has_error = True
        if username and ('�' in username or 'Ã' in username):
            has_error = True
        if group_name and ('�' in group_name or 'Ã' in group_name):
            has_error = True
            
        status = "❌" if has_error else "✅"
        print(f"{status} ID {user_id:4d} | {username:25s} | {full_name:35s} | {group_name or 'Sem grupo'}")
        
        if has_error:
            users_with_errors.append({
                'id': user_id,
                'username': username,
                'full_name': full_name,
                'group_name': group_name
            })
    
    print("\n" + "=" * 80)
    print(f"Total de usuários: {cursor.rowcount}")
    print(f"Usuários com erros: {len(users_with_errors)}")
    
    if users_with_errors:
        print("\n🔧 USUÁRIOS QUE PRECISAM DE CORREÇÃO:")
        print("-" * 80)
        for user in users_with_errors:
            print(f"ID {user['id']:4d}: {user['full_name']}")
    
    conn.close()

if __name__ == '__main__':
    main()
