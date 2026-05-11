#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar estrutura da tabela users e listar usuários
"""

import sqlite3

DB_PATH = 'ippel_system.db'

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ver estrutura da tabela users
    print("📊 ESTRUTURA DA TABELA USERS:")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]:20s} {col[2]:10s}")
    
    # Listar todos os usuários
    print("\n📋 USUÁRIOS NO BANCO DE DADOS:")
    print("=" * 100)
    cursor.execute("""
        SELECT u.id, u.name, g.name as grupo 
        FROM users u 
        LEFT JOIN groups g ON u.group_id = g.id 
        ORDER BY u.name
    """)
    
    users_with_errors = []
    
    for row in cursor.fetchall():
        user_id = row[0]
        name = row[1] if row[1] else ""
        group_name = row[2] if row[2] else "Sem grupo"
        
        # Detectar caracteres problemáticos
        has_error = ('�' in name or 'Ã' in name or '�' in group_name)
            
        status = "❌" if has_error else "✅"
        print(f"{status} ID {user_id:4d} | {name:45s} | {group_name}")
        
        if has_error:
            users_with_errors.append({
                'id': user_id,
                'name': name,
                'group_name': group_name
            })
    
    print("\n" + "=" * 100)
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    print(f"Total de usuários: {total}")
    print(f"Usuários com erros: {len(users_with_errors)}")
    
    if users_with_errors:
        print("\n🔧 USUÁRIOS QUE PRECISAM DE CORREÇÃO:")
        print("-" * 100)
        for user in users_with_errors:
            print(f"ID {user['id']:4d}: {user['name']}")
    
    conn.close()

if __name__ == '__main__':
    main()
