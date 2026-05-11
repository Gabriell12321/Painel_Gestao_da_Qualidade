#!/usr/bin/env python3
"""
Check for invalid employee names in the database
Specifically looking for 'lalinka' and '14321'
"""

import sqlite3

DB_PATH = 'ippel_system.db'

def check_invalid_employees():
    """Find RNCs with invalid employee names"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("CHECKING FOR INVALID EMPLOYEE NAMES")
    print("=" * 80)
    
    # Check for lalinka
    print("\n1. SEARCHING FOR 'lalinka':")
    cursor.execute("""
        SELECT rnc_number, responsavel, area_responsavel, setor, status, price
        FROM rncs
        WHERE LOWER(responsavel) LIKE '%lalinka%'
        OR LOWER(area_responsavel) LIKE '%lalinka%'
        OR LOWER(setor) LIKE '%lalinka%'
        ORDER BY rnc_number
    """)
    
    lalinka_rncs = cursor.fetchall()
    if lalinka_rncs:
        print(f"Found {len(lalinka_rncs)} RNCs with 'lalinka':")
        for rnc in lalinka_rncs:
            print(f"  RNC #{rnc['rnc_number']}")
            print(f"    Responsável: {rnc['responsavel']}")
            print(f"    Área Responsável: {rnc['area_responsavel']}")
            print(f"    Setor: {rnc['setor']}")
            print(f"    Status: {rnc['status']}")
            print(f"    Price: {rnc['price']}")
            print()
    else:
        print("  No RNCs found with 'lalinka'")
    
    # Check for 14321
    print("\n2. SEARCHING FOR '14321':")
    cursor.execute("""
        SELECT rnc_number, responsavel, area_responsavel, setor, status, price
        FROM rncs
        WHERE responsavel LIKE '%14321%'
        OR area_responsavel LIKE '%14321%'
        OR setor LIKE '%14321%'
        ORDER BY rnc_number
    """)
    
    num_rncs = cursor.fetchall()
    if num_rncs:
        print(f"Found {len(num_rncs)} RNCs with '14321':")
        for rnc in num_rncs:
            print(f"  RNC #{rnc['rnc_number']}")
            print(f"    Responsável: {rnc['responsavel']}")
            print(f"    Área Responsável: {rnc['area_responsavel']}")
            print(f"    Setor: {rnc['setor']}")
            print(f"    Status: {rnc['status']}")
            print(f"    Price: {rnc['price']}")
            print()
    else:
        print("  No RNCs found with '14321'")
    
    # Check for duplicate Engenharia (case variations) in area_responsavel
    print("\n3. CHECKING ENGENHARIA SECTOR VARIATIONS:")
    cursor.execute("""
        SELECT DISTINCT area_responsavel, COUNT(*) as count
        FROM rncs
        WHERE LOWER(area_responsavel) = 'engenharia'
        GROUP BY area_responsavel
        ORDER BY area_responsavel
    """)
    
    eng_variations = cursor.fetchall()
    if eng_variations:
        print(f"Found {len(eng_variations)} variations of 'Engenharia' in area_responsavel:")
        for var in eng_variations:
            print(f"  '{var['area_responsavel']}': {var['count']} RNCs")
    
    # Check setor field for variations
    cursor.execute("""
        SELECT DISTINCT setor, COUNT(*) as count
        FROM rncs
        WHERE LOWER(setor) LIKE '%engenharia%'
        GROUP BY setor
        ORDER BY setor
    """)
    
    setor_variations = cursor.fetchall()
    if setor_variations:
        print(f"\nFound {len(setor_variations)} variations in setor field:")
        for var in setor_variations:
            print(f"  '{var['setor']}': {var['count']} RNCs")
    
    # Get all unique responsavel names in Engenharia
    print("\n4. ALL EMPLOYEES IN ENGENHARIA (from area_responsavel):")
    cursor.execute("""
        SELECT DISTINCT responsavel, COUNT(*) as count
        FROM rncs
        WHERE LOWER(area_responsavel) = 'engenharia'
        AND status = 'Finalizado'
        AND responsavel IS NOT NULL
        AND responsavel != ''
        GROUP BY responsavel
        ORDER BY responsavel
    """)
    
    employees = cursor.fetchall()
    if employees:
        print(f"Found {len(employees)} unique employee names:")
        for emp in employees:
            name = emp['responsavel']
            count = emp['count']
            # Highlight suspicious names
            if name.lower() in ['lalinka', '14321'] or name.isdigit():
                print(f"  ⚠️  '{name}': {count} RNCs (SUSPICIOUS)")
            else:
                print(f"  '{name}': {count} RNCs")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    check_invalid_employees()
