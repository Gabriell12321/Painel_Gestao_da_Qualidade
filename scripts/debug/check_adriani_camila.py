#!/usr/bin/env python3
"""
Check Adriani Melotti and Camila Bettega in Engenharia
"""

import sqlite3

DB_PATH = 'ippel_system.db'

def check_employees():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("CHECKING ADRIANI MELOTTI AND CAMILA BETTEGA")
    print("=" * 80)
    
    # Check Adriani Melotti
    print("\n1. ADRIANI MELOTTI:")
    cursor.execute("""
        SELECT COUNT(*) as count,
               SUM(CAST(REPLACE(REPLACE(REPLACE(price, 'R$', ''), ' ', ''), ',', '.') AS REAL)) as total,
               area_responsavel
        FROM rncs
        WHERE LOWER(responsavel) LIKE '%adriani%melotti%'
        AND status = 'Finalizado'
        GROUP BY area_responsavel
    """)
    
    results = cursor.fetchall()
    for r in results:
        print(f"   {r['area_responsavel']}: {r['count']} RNCs - R$ {r['total']:.2f}" if r['total'] else f"   {r['area_responsavel']}: {r['count']} RNCs")
    
    # Check Camila Bettega
    print("\n2. CAMILA BETTEGA:")
    cursor.execute("""
        SELECT COUNT(*) as count,
               SUM(CAST(REPLACE(REPLACE(REPLACE(price, 'R$', ''), ' ', ''), ',', '.') AS REAL)) as total,
               area_responsavel
        FROM rncs
        WHERE LOWER(responsavel) LIKE '%camila%bettega%'
        AND status = 'Finalizado'
        GROUP BY area_responsavel
    """)
    
    results = cursor.fetchall()
    for r in results:
        print(f"   {r['area_responsavel']}: {r['count']} RNCs - R$ {r['total']:.2f}" if r['total'] else f"   {r['area_responsavel']}: {r['count']} RNCs")
    
    # Check all employees in Engenharia
    print("\n3. CHECKING IF THEY SHOULD BE IN ENGENHARIA:")
    
    # Check user table
    cursor.execute("""
        SELECT id, name, department 
        FROM users 
        WHERE LOWER(name) LIKE '%adriani%melotti%' 
        OR LOWER(name) LIKE '%camila%bettega%'
    """)
    
    users = cursor.fetchall()
    if users:
        for u in users:
            print(f"   User: {u['name']} - Department: {u['department']}")
    else:
        print("   Not found in users table")
    
    # Sample RNCs
    print("\n4. SAMPLE RNCs FROM ADRIANI MELOTTI:")
    cursor.execute("""
        SELECT rnc_number, responsavel, area_responsavel, setor, price
        FROM rncs
        WHERE LOWER(responsavel) LIKE '%adriani%melotti%'
        AND status = 'Finalizado'
        LIMIT 5
    """)
    
    samples = cursor.fetchall()
    for rnc in samples:
        print(f"   RNC #{rnc['rnc_number']}: {rnc['area_responsavel']} / {rnc['setor']} - {rnc['price']}")
    
    print("\n5. SAMPLE RNCs FROM CAMILA BETTEGA:")
    cursor.execute("""
        SELECT rnc_number, responsavel, area_responsavel, setor, price
        FROM rncs
        WHERE LOWER(responsavel) LIKE '%camila%bettega%'
        AND status = 'Finalizado'
        LIMIT 5
    """)
    
    samples = cursor.fetchall()
    for rnc in samples:
        print(f"   RNC #{rnc['rnc_number']}: {rnc['area_responsavel']} / {rnc['setor']} - {rnc['price']}")
    
    conn.close()
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    check_employees()
