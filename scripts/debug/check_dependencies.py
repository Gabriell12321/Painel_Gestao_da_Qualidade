#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de verificação de dependências e compatibilidade
Para diagnosticar problemas entre ambiente local e produção
"""

import sys
import importlib.metadata

def check_version(package_name, expected_version=None):
    """Verifica versão de um pacote"""
    try:
        version = importlib.metadata.version(package_name)
        status = "✓" if not expected_version or version == expected_version else "⚠"
        print(f"{status} {package_name:25s} {version:15s} {'(esperado: ' + expected_version + ')' if expected_version and version != expected_version else ''}")
        return True, version
    except importlib.metadata.PackageNotFoundError:
        print(f"✗ {package_name:25s} NÃO INSTALADO")
        return False, None

def check_imports():
    """Verifica se imports críticos funcionam"""
    print("\n=== IMPORTS CRÍTICOS ===")
    critical_imports = [
        ('flask', 'Flask'),
        ('flask_socketio', 'SocketIO'),
        ('werkzeug.security', 'check_password_hash'),
        ('sqlite3', None),
        ('json', None),
        ('datetime', 'datetime'),
    ]
    
    for module_name, attr_name in critical_imports:
        try:
            module = importlib.import_module(module_name)
            if attr_name:
                getattr(module, attr_name)
            print(f"✓ {module_name:30s} OK")
        except Exception as e:
            print(f"✗ {module_name:30s} ERRO: {e}")

def check_database():
    """Verifica se o banco de dados está acessível"""
    print("\n=== BANCO DE DADOS ===")
    try:
        import sqlite3
        conn = sqlite3.connect('ippel_system.db')
        cursor = conn.cursor()
        
        # Verificar tabelas principais
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"✓ Banco acessível: {len(tables)} tabelas encontradas")
        
        # Verificar tabela rncs
        if 'rncs' in tables:
            cursor.execute("SELECT COUNT(*) FROM rncs")
            count = cursor.fetchone()[0]
            print(f"✓ Tabela 'rncs': {count} registros")
        else:
            print("✗ Tabela 'rncs' NÃO EXISTE")
        
        # Verificar tabela ros
        if 'ros' in tables:
            cursor.execute("SELECT COUNT(*) FROM ros")
            count = cursor.fetchone()[0]
            print(f"✓ Tabela 'ros': {count} registros")
        else:
            print("✗ Tabela 'ros' NÃO EXISTE")
        
        conn.close()
    except Exception as e:
        print(f"✗ Erro ao acessar banco: {e}")

def main():
    print("=" * 70)
    print("VERIFICAÇÃO DE DEPENDÊNCIAS E COMPATIBILIDADE")
    print("=" * 70)
    
    print(f"\nPython: {sys.version}")
    print(f"Plataforma: {sys.platform}")
    
    print("\n=== DEPENDÊNCIAS PRINCIPAIS ===")
    
    # Dependências do requirements.txt
    dependencies = {
        'flask': '2.3.3',
        'flask-login': '0.6.3',
        'Werkzeug': '2.3.7',
        'Jinja2': '3.1.2',
        'flask-socketio': '5.5.1',
        'python-socketio': '5.13.0',
        'redis': '5.0.8',
        'Flask-Compress': '1.15',
        'brotli': '1.1.0',
        'Flask-Limiter': '3.8.0',
        'flask-talisman': '1.1.0',
        'Pillow': '10.4.0',
        'PyJWT': '2.9.0',
        'requests': '2.32.3',
    }
    
    incompatible = []
    missing = []
    
    for package, expected_version in dependencies.items():
        installed, version = check_version(package, expected_version)
        if not installed:
            missing.append(package)
        elif version != expected_version:
            incompatible.append((package, version, expected_version))
    
    check_imports()
    check_database()
    
    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    
    if missing:
        print(f"\n⚠ PACOTES FALTANDO ({len(missing)}):")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nInstalação:")
        print(f"  pip install {' '.join(missing)}")
    
    if incompatible:
        print(f"\n⚠ VERSÕES INCOMPATÍVEIS ({len(incompatible)}):")
        for pkg, installed, expected in incompatible:
            print(f"  - {pkg}: instalado={installed}, esperado={expected}")
        print("\nAtualização:")
        for pkg, _, expected in incompatible:
            print(f"  pip install {pkg}=={expected}")
    
    if not missing and not incompatible:
        print("\n✓ TODAS AS DEPENDÊNCIAS OK")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
