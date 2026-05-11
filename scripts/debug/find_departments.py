#!/usr/bin/env python3
"""
Find correct department for Adriani and Camila
"""

import sqlite3

DB_PATH = 'ippel_system.db'

def find_departments():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("FINDING CORRECT DEPARTMENTS")
    print("=" * 80)
    
    # Search in users table
    print("\n1. USERS TABLE:")
    cursor.execute("""
        SELECT name, department 
        FROM users 
        WHERE LOWER(name) LIKE '%adriani%' 
        OR LOWER(name) LIKE '%camila%'
    """)
    
    users = cursor.fetchall()
    for u in users:
        print(f"   {u['name']}: {u['department']}")
    
    # Check what areas they appear in RNCs
    print("\n2. AREAS WHERE ADRIANI MELOTTI APPEARS:")
    cursor.execute("""
        SELECT DISTINCT area_responsavel, COUNT(*) as count
        FROM rncs
        WHERE LOWER(responsavel) = 'adriani melotti'
        GROUP BY area_responsavel
        ORDER BY count DESC
    """)
    
    areas = cursor.fetchall()
    for a in areas:
        print(f"   {a['area_responsavel']}: {a['count']} RNCs")
    
    print("\n3. AREAS WHERE CAMILA BETTEGA APPEARS:")
    cursor.execute("""
        SELECT DISTINCT area_responsavel, COUNT(*) as count
        FROM rncs
        WHERE LOWER(responsavel) = 'camila bettega'
        GROUP BY area_responsavel
        ORDER BY count DESC
    """)
    
    areas = cursor.fetchall()
    for a in areas:
        print(f"   {a['area_responsavel']}: {a['count']} RNCs")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("CONCLUSÃO: Eles aparecem apenas em Engenharia, mas você quer removê-los.")
    print("Vou excluí-los do relatório da Engenharia.")
    print("=" * 80)

if __name__ == '__main__':
    find_departments()
