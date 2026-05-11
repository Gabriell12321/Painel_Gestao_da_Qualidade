#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar a correção do JOIN de area_responsavel
Verifica se está pegando o nome do grupo ao invés do ID
"""

import sqlite3

DB_PATH = 'ippel_system.db'

def test_area_responsavel_query():
    """Testa a query corrigida"""
    print("=" * 80)
    print("TESTE: Query corrigida para area_responsavel")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Query ANTIGA (incorreta - só pegava IDs)
    print("\n1. Query ANTIGA (incorreta):")
    cursor.execute('''
        SELECT r.id, r.rnc_number, r.area_responsavel,
               g.name as area_responsavel_name
        FROM rncs r
        LEFT JOIN groups g ON CAST(r.area_responsavel AS INTEGER) = g.id
        WHERE r.area_responsavel IS NOT NULL
        LIMIT 10
    ''')
    
    print("\nRNC_ID | RNC_NUM | area_responsavel | area_responsavel_name (antiga)")
    print("-" * 80)
    for row in cursor.fetchall():
        print(f"{row[0]:6} | {row[1]:7} | {str(row[2]):20} | {row[3] or 'NULL'}")
    
    # Query NOVA (corrigida - pega IDs e nomes)
    print("\n\n2. Query NOVA (corrigida):")
    cursor.execute('''
        SELECT r.id, r.rnc_number, r.area_responsavel,
               COALESCE(g1.name, g2.name, r.area_responsavel) as area_responsavel_name
        FROM rncs r
        LEFT JOIN groups g1 ON (r.area_responsavel GLOB '[0-9]*' AND CAST(r.area_responsavel AS INTEGER) = g1.id)
        LEFT JOIN groups g2 ON (r.area_responsavel NOT GLOB '[0-9]*' AND LOWER(TRIM(r.area_responsavel)) = LOWER(TRIM(g2.name)))
        WHERE r.area_responsavel IS NOT NULL
        LIMIT 10
    ''')
    
    print("\nRNC_ID | RNC_NUM | area_responsavel | area_responsavel_name (nova)")
    print("-" * 80)
    for row in cursor.fetchall():
        print(f"{row[0]:6} | {row[1]:7} | {str(row[2]):20} | {row[3]}")
    
    # Verificar grupos disponíveis
    print("\n\n3. Grupos disponíveis no sistema:")
    cursor.execute('SELECT id, name FROM groups ORDER BY id')
    print("\nID | Nome do Grupo")
    print("-" * 40)
    for row in cursor.fetchall():
        print(f"{row[0]:2} | {row[1]}")
    
    # Estatísticas
    print("\n\n4. Estatísticas:")
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN area_responsavel GLOB '[0-9]*' THEN 1 END) as com_id,
            COUNT(CASE WHEN area_responsavel NOT GLOB '[0-9]*' THEN 1 END) as com_nome
        FROM rncs
        WHERE area_responsavel IS NOT NULL
    ''')
    stats = cursor.fetchone()
    print(f"Total RNCs com area_responsavel: {stats[0]}")
    print(f"  - Com ID numérico: {stats[1]}")
    print(f"  - Com nome/texto: {stats[2]}")
    
    # Testar busca específica por ID "11" (PCP)
    print("\n\n5. Teste específico: área_responsavel = '11' (PCP):")
    cursor.execute('''
        SELECT r.id, r.rnc_number, r.area_responsavel,
               COALESCE(g1.name, g2.name, r.area_responsavel) as area_responsavel_name
        FROM rncs r
        LEFT JOIN groups g1 ON (r.area_responsavel GLOB '[0-9]*' AND CAST(r.area_responsavel AS INTEGER) = g1.id)
        LEFT JOIN groups g2 ON (r.area_responsavel NOT GLOB '[0-9]*' AND LOWER(TRIM(r.area_responsavel)) = LOWER(TRIM(g2.name)))
        WHERE r.area_responsavel = '11'
        LIMIT 5
    ''')
    
    print("\nRNC_ID | RNC_NUM | area_responsavel | area_responsavel_name")
    print("-" * 80)
    for row in cursor.fetchall():
        print(f"{row[0]:6} | {row[1]:7} | {str(row[2]):20} | {row[3]}")
    
    conn.close()
    print("\n" + "=" * 80)
    print("✅ Teste concluído! Se '11' mostrar 'PCP', a correção funcionou.")
    print("=" * 80)

if __name__ == '__main__':
    test_area_responsavel_query()
