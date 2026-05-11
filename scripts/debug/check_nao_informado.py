#!/usr/bin/env python3
"""
Check for 'Não informado' in the database
"""

import sqlite3

DB_PATH = 'ippel_system.db'

def check_nao_informado():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("CHECKING FOR 'Não informado'")
    print("=" * 80)
    
    # Check in responsavel
    print("\n1. In 'responsavel' field:")
    cursor.execute("""
        SELECT COUNT(*) as count, SUM(CAST(REPLACE(REPLACE(REPLACE(price, 'R$', ''), ' ', ''), ',', '.') AS REAL)) as total
        FROM rncs
        WHERE responsavel = 'Não informado'
        AND status = 'Finalizado'
    """)
    result = cursor.fetchone()
    print(f"   Found: {result['count']} RNCs")
    print(f"   Total value: R$ {result['total']:.2f}" if result['total'] else "   Total value: R$ 0,00")
    
    # Check in area_responsavel
    print("\n2. In 'area_responsavel' field:")
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM rncs
        WHERE area_responsavel = 'Não informado'
        AND status = 'Finalizado'
    """)
    result = cursor.fetchone()
    print(f"   Found: {result['count']} RNCs")
    
    # Check in setor
    print("\n3. In 'setor' field:")
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM rncs
        WHERE setor = 'Não informado'
        AND status = 'Finalizado'
    """)
    result = cursor.fetchone()
    print(f"   Found: {result['count']} RNCs")
    
    # Check for NULL or empty responsavel
    print("\n4. NULL or empty 'responsavel':")
    cursor.execute("""
        SELECT COUNT(*) as count, SUM(CAST(REPLACE(REPLACE(REPLACE(price, 'R$', ''), ' ', ''), ',', '.') AS REAL)) as total
        FROM rncs
        WHERE (responsavel IS NULL OR responsavel = '' OR responsavel = ' ')
        AND status = 'Finalizado'
    """)
    result = cursor.fetchone()
    print(f"   Found: {result['count']} RNCs")
    print(f"   Total value: R$ {result['total']:.2f}" if result['total'] else "   Total value: R$ 0,00")
    
    # Show sample RNCs
    print("\n5. Sample RNCs with 'Não informado' or NULL responsavel:")
    cursor.execute("""
        SELECT rnc_number, responsavel, area_responsavel, setor, price
        FROM rncs
        WHERE (responsavel = 'Não informado' OR responsavel IS NULL OR responsavel = '')
        AND status = 'Finalizado'
        LIMIT 10
    """)
    
    samples = cursor.fetchall()
    for rnc in samples:
        print(f"   RNC #{rnc['rnc_number']}: '{rnc['responsavel']}' - {rnc['area_responsavel']} - R$ {rnc['price']}")
    
    conn.close()
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    check_nao_informado()
