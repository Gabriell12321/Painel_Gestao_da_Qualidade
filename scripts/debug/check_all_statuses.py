#!/usr/bin/env python3
"""
Check all RNCs from Adriani and Camila (Finalizadas + Ativas)
"""

import sqlite3

DB_PATH = 'ippel_system.db'

def check_all_rncs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("VERIFICANDO TODOS OS STATUS DE RNCs")
    print("=" * 80)
    
    # Check all statuses
    print("\n1. ADRIANI MELOTTI - TODOS OS STATUS:")
    cursor.execute("""
        SELECT status, COUNT(*) as count,
               SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(price, 'R$', ''), ' ', ''), ',', '.'), '"', '') AS REAL)) as total
        FROM rncs
        WHERE LOWER(responsavel) = 'adriani melotti'
        GROUP BY status
        ORDER BY status
    """)
    
    adriani_status = cursor.fetchall()
    total_adriani = 0
    valor_adriani = 0
    for s in adriani_status:
        valor = s['total'] if s['total'] else 0
        print(f"   {s['status']}: {s['count']} RNCs - R$ {valor:.2f}")
        total_adriani += s['count']
        valor_adriani += valor
    print(f"   TOTAL: {total_adriani} RNCs - R$ {valor_adriani:.2f}")
    
    print("\n2. CAMILA BETTEGA - TODOS OS STATUS:")
    cursor.execute("""
        SELECT status, COUNT(*) as count,
               SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(price, 'R$', ''), ' ', ''), ',', '.'), '"', '') AS REAL)) as total
        FROM rncs
        WHERE LOWER(responsavel) = 'camila bettega'
        GROUP BY status
        ORDER BY status
    """)
    
    camila_status = cursor.fetchall()
    total_camila = 0
    valor_camila = 0
    for s in camila_status:
        valor = s['total'] if s['total'] else 0
        print(f"   {s['status']}: {s['count']} RNCs - R$ {valor:.2f}")
        total_camila += s['count']
        valor_camila += valor
    print(f"   TOTAL: {total_camila} RNCs - R$ {valor_camila:.2f}")
    
    # Check current query used in reports
    print("\n" + "=" * 80)
    print("\n3. QUERY ATUAL DO RELATÓRIO (Finalizado + responsavel definido):")
    cursor.execute("""
        SELECT COUNT(*) as count,
               SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(price, 'R$', ''), ' ', ''), ',', '.'), '"', '') AS REAL)) as total
        FROM rncs
        WHERE is_deleted = 0 
        AND status = 'Finalizado'
        AND responsavel IS NOT NULL
        AND responsavel != ''
        AND LOWER(responsavel) NOT IN ('adriani melotti', 'camila bettega')
    """)
    
    current = cursor.fetchone()
    print(f"   RNCs no relatório: {current['count']}")
    print(f"   Valor total: R$ {current['total']:.2f}" if current['total'] else "   Valor total: R$ 0,00")
    
    # Sample of active RNCs
    print("\n4. AMOSTRA DE RNCs ATIVAS (não Finalizadas):")
    cursor.execute("""
        SELECT rnc_number, responsavel, status, area_responsavel, price
        FROM rncs
        WHERE status != 'Finalizado'
        AND responsavel IS NOT NULL
        AND responsavel != ''
        LIMIT 10
    """)
    
    samples = cursor.fetchall()
    if samples:
        for rnc in samples:
            print(f"   RNC #{rnc['rnc_number']}: {rnc['responsavel']} - {rnc['status']} - {rnc['area_responsavel']} - {rnc['price']}")
    else:
        print("   Nenhuma RNC ativa encontrada")
    
    # Check all distinct statuses
    print("\n5. TODOS OS STATUS EXISTENTES NO SISTEMA:")
    cursor.execute("""
        SELECT DISTINCT status, COUNT(*) as count
        FROM rncs
        WHERE is_deleted = 0
        GROUP BY status
        ORDER BY count DESC
    """)
    
    statuses = cursor.fetchall()
    for s in statuses:
        print(f"   {s['status']}: {s['count']} RNCs")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("PROBLEMA IDENTIFICADO: O relatório só mostra RNCs 'Finalizado'")
    print("SOLUÇÃO: Incluir todos os status ou criar filtro para status")
    print("=" * 80)

if __name__ == '__main__':
    check_all_rncs()
