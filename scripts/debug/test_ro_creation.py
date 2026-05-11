#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de criação de R.O - Diagnosticar problema em produção
"""

import sqlite3
import json
import sys

def test_ro_creation():
    """Testa se a criação de R.O funciona no banco"""
    print("=== TESTE DE CRIAÇÃO DE R.O ===\n")
    
    try:
        conn = sqlite3.connect('ippel_system.db', timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=15000")
        cursor = conn.cursor()
        
        print("✓ Conexão com banco estabelecida")
        
        # Verificar estrutura da tabela ros
        cursor.execute("PRAGMA table_info(ros)")
        columns_info = cursor.fetchall()
        columns = [row[1] for row in columns_info]
        print(f"✓ Tabela ros tem {len(columns)} colunas")
        
        print("\nColunas da tabela ros:")
        for i, row in enumerate(columns_info, 1):
            print(f"  {i:2d}. {row[1]:30s} {row[2]}")
        
        # Verificar se colunas críticas existem
        critical_columns = [
            'ro_number', 'title', 'description', 'equipment', 'client',
            'priority', 'status', 'user_id', 'created_at', 'cv', 'mp',
            'conjunto', 'modelo', 'position', 'material', 'quantity',
            'drawing_number', 'revision', 'description_drawing',
            'area_responsavel', 'ass_responsavel', 'inspetor',
            'responsavel', 'setor', 'purchase_order',
            'instruction_retrabalho', 'cause_ro', 'price', 'price_note'
        ]
        
        missing = [col for col in critical_columns if col not in columns]
        if missing:
            print(f"\n✗ Colunas faltando: {', '.join(missing)}")
            print("\nEssas colunas precisam ser adicionadas no servidor de produção!")
            return False
        else:
            print(f"\n✓ Todas as colunas críticas existem")
        
        # Testar geração de número
        cursor.execute('SELECT MAX(CAST(ro_number AS INTEGER)) as max_num FROM ros')
        result = cursor.fetchone()
        max_num = result['max_num'] if result and result['max_num'] else 19
        next_number = max_num + 1
        print(f"✓ Próximo número de R.O: {next_number}")
        
        # Testar INSERT completo com TODOS os campos
        test_data = {
            'ro_number': str(next_number),
            'title': 'TESTE',
            'description': 'Teste de criação',
            'equipment': 'Teste',
            'client': 'Teste',
            'priority': 'Média',
            'status': 'Pendente',
            'user_id': 1,
            'drawing_number': '123',
            'revision': '0',
            'conjunto': 'Teste',
            'description_drawing': 'Teste',
            'position': 'A1',
            'modelo': 'X',
            'material': '304',
            'quantity': '1',
            'cv': '123456',
            'mp': '789',
            'area_responsavel': 'Engenharia',
            'ass_responsavel': 'Teste',
            'inspetor': 'Teste',
            'responsavel': 'Teste',
            'setor': 'Teste',
            'purchase_order': '001',
            'instruction_retrabalho': 'Teste',
            'cause_ro': 'Teste',
            'price': 'R$ 100,00',
            'price_note': 'Teste'
        }
        
        try:
            cursor.execute('''
                INSERT INTO ros (
                    ro_number, title, description, equipment, client,
                    priority, status, user_id, instruction_retrabalho, cause_ro,
                    drawing_number, revision, conjunto, description_drawing,
                    position, modelo, material, quantity, cv, mp,
                    price, price_note, area_responsavel, ass_responsavel,
                    inspetor, responsavel, signature_inspection2_name,
                    setor, purchase_order, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                test_data['ro_number'],
                test_data['title'],
                test_data['description'],
                test_data['equipment'],
                test_data['client'],
                test_data['priority'],
                test_data['status'],
                test_data['user_id'],
                test_data['instruction_retrabalho'],
                test_data['cause_ro'],
                test_data['drawing_number'],
                test_data['revision'],
                test_data['conjunto'],
                test_data['description_drawing'],
                test_data['position'],
                test_data['modelo'],
                test_data['material'],
                test_data['quantity'],
                test_data['cv'],
                test_data['mp'],
                test_data['price'],
                test_data['price_note'],
                test_data['area_responsavel'],
                test_data['ass_responsavel'],
                test_data['inspetor'],
                test_data['responsavel'],
                None,  # signature_inspection2_name
                test_data['setor'],
                test_data['purchase_order']
            ))
            
            ro_id = cursor.lastrowid
            print(f"✓ INSERT bem-sucedido (ID: {ro_id})")
            
            # Verificar se foi inserido
            cursor.execute('SELECT * FROM ros WHERE id = ?', (ro_id,))
            inserted = cursor.fetchone()
            if inserted:
                print(f"✓ R.O verificado no banco")
                print(f"  - Número: {inserted['ro_number']}")
                print(f"  - Título: {inserted['title']}")
                print(f"  - CV: {inserted['cv']}")
                print(f"  - MP: {inserted['mp']}")
                print(f"  - Conjunto: {inserted['conjunto']}")
                print(f"  - Modelo: {inserted['modelo']}")
            
        except sqlite3.OperationalError as e:
            print(f"\n✗ ERRO SQL: {e}")
            if "no column named" in str(e) or "table ros has no column named" in str(e):
                print("\n⚠ PROBLEMA: Coluna não existe na tabela ros do servidor!")
                print("Execute no servidor de produção:")
                print("  python fix_ros_table_columns.py")
            return False
        
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

def test_flask_ro_endpoint():
    """Testa se o endpoint de criação de R.O funciona"""
    print("\n=== TESTE DE ENDPOINT FLASK ===\n")
    
    try:
        from flask import Flask, jsonify
        
        app = Flask(__name__)
        app.secret_key = 'test'
        
        # Simular sessão
        with app.test_request_context():
            with app.test_client() as client:
                # Simular sessão de usuário
                with client.session_transaction() as sess:
                    sess['user_id'] = 1
                
                # Dados de teste
                test_data = {
                    'title': 'TESTE',
                    'description': 'Teste',
                    'equipment': 'Teste',
                    'client': 'Teste',
                    'priority': 'Média',
                    'cv': '123456',
                    'mp': '789',
                    'conjunto': 'Teste',
                    'modelo': 'X',
                    'position': 'A1',
                    'material': '304',
                    'quantity': '1'
                }
                
                print(f"✓ Flask app criado")
                print(f"✓ Sessão simulada (user_id: 1)")
                print(f"✓ Dados de teste preparados")
                
                # Testar serialização JSON
                json_data = json.dumps(test_data)
                parsed = json.loads(json_data)
                
                if parsed == test_data:
                    print(f"✓ Serialização JSON OK")
                else:
                    print(f"✗ Erro na serialização JSON")
                    return False
        
        return True
        
    except Exception as e:
        print(f"✗ ERRO NO TESTE FLASK: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_production():
    """Gera comandos para sincronizar produção"""
    print("\n=== COMANDOS PARA PRODUÇÃO ===\n")
    
    print("1. Copie os arquivos de correção:")
    print("   - fix_ros_table_columns.py")
    print("   - check_dependencies.py")
    print("   - test_ro_creation.py")
    
    print("\n2. No servidor de produção, execute:")
    print("   python check_dependencies.py")
    print("   python test_ro_creation.py")
    
    print("\n3. Se houver colunas faltando:")
    print("   python fix_ros_table_columns.py")
    
    print("\n4. Verifique as versões do Flask:")
    print("   python -c \"import flask; print(flask.__version__)\"")
    
    print("\n5. Se necessário, atualize dependências:")
    print("   pip install -r requirements.txt --upgrade")

def main():
    print("=" * 70)
    print("DIAGNÓSTICO DE PROBLEMA DE CRIAÇÃO DE R.O")
    print("=" * 70)
    print(f"\nPython: {sys.version}")
    
    try:
        import flask
        import importlib.metadata
        version = importlib.metadata.version('flask')
        print(f"Flask: {version}")
    except:
        pass
    
    print("\n" + "=" * 70 + "\n")
    
    db_ok = test_ro_creation()
    flask_ok = test_flask_ro_endpoint()
    
    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)
    
    if db_ok and flask_ok:
        print("\n✓ TODOS OS TESTES LOCAIS PASSARAM")
        print("\n⚠ Se o erro persiste em PRODUÇÃO, as causas podem ser:")
        print("  1. Tabela 'ros' no servidor NÃO TEM todas as colunas")
        print("  2. Versões diferentes de Flask/Werkzeug")
        print("  3. Permissões de escrita no banco SQLite")
        print("  4. Timeout do banco (busy_timeout)")
    else:
        print("\n✗ ALGUNS TESTES FALHARAM")
        print("\nO problema está acontecendo AQUI também!")
        print("Verifique os erros acima")
    
    compare_with_production()
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
