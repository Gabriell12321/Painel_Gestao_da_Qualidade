#!/usr/bin/env python3
"""
List all RNCs from Adriani Melotti and Camila Bettega
"""

import sqlite3

DB_PATH = 'ippel_system.db'

def list_rncs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("RNCs DE ADRIANI MELOTTI E CAMILA BETTEGA")
    print("=" * 80)
    
    # Adriani Melotti
    print("\n1. ADRIANI MELOTTI:")
    cursor.execute("""
        SELECT rnc_number, title, area_responsavel, setor, status, price, created_at
        FROM rncs
        WHERE LOWER(responsavel) = 'adriani melotti'
        ORDER BY created_at DESC
    """)
    
    adriani_rncs = cursor.fetchall()
    print(f"\nTotal: {len(adriani_rncs)} RNCs\n")
    
    for rnc in adriani_rncs:
        print(f"RNC #{rnc['rnc_number']}")
        print(f"  Título: {rnc['title']}")
        print(f"  Área: {rnc['area_responsavel']}")
        print(f"  Setor: {rnc['setor']}")
        print(f"  Status: {rnc['status']}")
        print(f"  Valor: {rnc['price']}")
        print(f"  Criada em: {rnc['created_at']}")
        print()
    
    # Camila Bettega
    print("\n" + "=" * 80)
    print("\n2. CAMILA BETTEGA:")
    cursor.execute("""
        SELECT rnc_number, title, area_responsavel, setor, status, price, created_at
        FROM rncs
        WHERE LOWER(responsavel) = 'camila bettega'
        ORDER BY created_at DESC
        LIMIT 50
    """)
    
    camila_rncs = cursor.fetchall()
    
    # Count total
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM rncs
        WHERE LOWER(responsavel) = 'camila bettega'
    """)
    total_camila = cursor.fetchone()['total']
    
    print(f"\nTotal: {total_camila} RNCs (mostrando primeiras 50)\n")
    
    for rnc in camila_rncs:
        print(f"RNC #{rnc['rnc_number']}")
        print(f"  Título: {rnc['title']}")
        print(f"  Área: {rnc['area_responsavel']}")
        print(f"  Setor: {rnc['setor']}")
        print(f"  Status: {rnc['status']}")
        print(f"  Valor: {rnc['price']}")
        print(f"  Criada em: {rnc['created_at']}")
        print()
    
    # Summary by status
    print("\n" + "=" * 80)
    print("\n3. RESUMO POR STATUS:")
    
    cursor.execute("""
        SELECT responsavel, status, COUNT(*) as count,
               SUM(CAST(REPLACE(REPLACE(REPLACE(price, 'R$', ''), ' ', ''), ',', '.') AS REAL)) as total
        FROM rncs
        WHERE LOWER(responsavel) IN ('adriani melotti', 'camila bettega')
        GROUP BY responsavel, status
        ORDER BY responsavel, status
    """)
    
    summary = cursor.fetchall()
    for s in summary:
        valor = f"R$ {s['total']:.2f}" if s['total'] else "R$ 0,00"
        print(f"  {s['responsavel']} - {s['status']}: {s['count']} RNCs - {valor}")
    
    conn.close()
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    list_rncs()
