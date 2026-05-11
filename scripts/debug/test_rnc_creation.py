#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de criação de RNC - Diagnosticar problema em produção
"""

import sqlite3
import json
import sys

def test_rnc_creation():
    """Testa se a criação de RNC funciona no banco"""
    print("=== TESTE DE CRIAÇÃO DE RNC ===\n")
    
    try:
        conn = sqlite3.connect('ippel_system.db', timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=15000")
        cursor = conn.cursor()
        
        print("✓ Conexão com banco estabelecida")
        
        # Verificar estrutura da tabela rncs
        cursor.execute("PRAGMA table_info(rncs)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"✓ Tabela rncs tem {len(columns)} colunas")
        
        # Verificar se colunas críticas existem
        critical_columns = [
            'rnc_number', 'title', 'description', 'equipment', 'client',
            'priority', 'status', 'user_id', 'created_at', 'responsavel',
            'area_responsavel', 'setor', 'price'
        ]
        
        missing = [col for col in critical_columns if col not in columns]
        if missing:
            print(f"✗ Colunas faltando: {', '.join(missing)}")
            return False
        else:
            print(f"✓ Todas as colunas críticas existem")
        
        # Testar geração de número
        cursor.execute('SELECT MAX(CAST(rnc_number AS INTEGER)) as max_num FROM rncs')
        result = cursor.fetchone()
        max_num = result['max_num'] if result and result['max_num'] else 0
        next_number = max_num + 1
        print(f"✓ Próximo número de RNC: {next_number}")
        
        # Testar INSERT (sem commit - apenas verificação)
        test_data = {
            'rnc_number': str(next_number),
            'title': 'TESTE',
            'description': 'Teste de criação',
            'equipment': 'Teste',
            'client': 'Teste',
            'priority': 'Média',
            'status': 'Pendente',
            'user_id': 1
        }
        
        cursor.execute('''
            INSERT INTO rncs (
                rnc_number, title, description, equipment, client,
                priority, status, user_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            test_data['rnc_number'],
            test_data['title'],
            test_data['description'],
            test_data['equipment'],
            test_data['client'],
            test_data['priority'],
            test_data['status'],
            test_data['user_id']
        ))
        
        rnc_id = cursor.lastrowid
        print(f"✓ INSERT bem-sucedido (ID: {rnc_id})")
        
        # Verificar se foi inserido
        cursor.execute('SELECT * FROM rncs WHERE id = ?', (rnc_id,))
        inserted = cursor.fetchone()
        if inserted:
            print(f"✓ RNC verificado no banco")
            print(f"  - Número: {inserted['rnc_number']}")
            print(f"  - Título: {inserted['title']}")
        
        # ROLLBACK - não commitamos o teste
        conn.rollback()
        print("\n✓ TESTE CONCLUÍDO COM SUCESSO (rollback executado)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n✗ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_json():
    """Testa compatibilidade com jsonify do Flask"""
    print("\n=== TESTE DE COMPATIBILIDADE FLASK ===\n")
    
    try:
        from flask import Flask, jsonify
        
        app = Flask(__name__)
        
        with app.app_context():
            # Testar jsonify com dados de RNC
            test_response = {
                'success': True,
                'rnc_id': 12345,
                'rnc_number': '10001',
                'message': 'RNC criado com sucesso'
            }
            
            response = jsonify(test_response)
            print(f"✓ jsonify() funciona corretamente")
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.content_type}")
            
            # Verificar se o JSON é válido
            data = json.loads(response.get_data(as_text=True))
            if data == test_response:
                print(f"✓ JSON serialização/deserialização OK")
            else:
                print(f"✗ JSON não corresponde aos dados originais")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ ERRO NO TESTE FLASK: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 70)
    print("DIAGNÓSTICO DE PROBLEMA DE CRIAÇÃO DE RNC")
    print("=" * 70)
    print(f"\nPython: {sys.version}")
    
    try:
        import flask
        print(f"Flask: {flask.__version__ if hasattr(flask, '__version__') else 'versão não disponível'}")
    except:
        pass
    
    print("\n" + "=" * 70 + "\n")
    
    db_ok = test_rnc_creation()
    flask_ok = test_flask_json()
    
    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)
    
    if db_ok and flask_ok:
        print("\n✓ TODOS OS TESTES PASSARAM")
        print("\nSe ainda houver problema em produção, verifique:")
        print("  1. Permissões do usuário no banco de dados")
        print("  2. Logs do servidor Flask")
        print("  3. Firewall/SELinux bloqueando escrita no banco")
        print("  4. Versões das dependências (Flask 2.3 vs 3.1)")
    else:
        print("\n✗ ALGUNS TESTES FALHARAM")
        print("\nVerifique os erros acima e compare com o servidor de produção")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
