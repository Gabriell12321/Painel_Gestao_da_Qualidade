#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar erros de português em todos os templates
"""

import os
import re
from pathlib import Path

def check_portuguese_errors(file_path):
    """Verifica erros de português em um arquivo"""
    
    errors = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except:
        return errors
    
    # Padrões de erros comuns
    patterns = [
        (r'\bo\s+RNC\b', 'a RNC', 'RNC é feminino'),
        (r'\bNovo\s+RNC\b', 'Nova RNC', 'RNC é feminino'),
        (r'\bNenhum\s+RNC\b', 'Nenhuma RNC', 'RNC é feminino'),
        (r'\bdeletar\b', 'excluir', 'Forma mais correta'),
        (r'\bDeletar\b', 'Excluir', 'Forma mais correta'),
        (r'\bRNC\s+encontrado\b', 'RNC encontrada', 'RNC é feminino'),
        (r'\bRNC\s+não\s+encontrado\b', 'RNC não encontrada', 'RNC é feminino'),
        (r'N�o\s+Definidos', 'Não Definidos', 'Encoding incorreto'),
        (r'Produ��o', 'Produção', 'Encoding incorreto'),
        (r'Usin\.\s+Cil�ndrica', 'Usinagem Cilíndrica', 'Encoding incorreto'),
        (r'�', '[CARACTERE INVÁLIDO]', 'Problema de encoding'),
    ]
    
    for line_num, line in enumerate(lines, 1):
        # Ignorar linhas de comentário JavaScript/CSS
        if line.strip().startswith(('//','/*','*','<!--')):
            continue
            
        for pattern, correction, reason in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                errors.append({
                    'line': line_num,
                    'text': line.strip()[:100],
                    'pattern': pattern,
                    'correction': correction,
                    'reason': reason
                })
    
    return errors

def main():
    templates_dir = Path('templates')
    
    # Arquivos principais para verificar
    main_files = [
        'dashboard.html',
        'new_rnc.html',
        'edit_rnc.html',
        'view_rnc.html',
        'indicadores_dashboard.html',
        'login.html',
    ]
    
    print("=" * 100)
    print("🔍 VERIFICAÇÃO COMPLETA DE ERROS DE PORTUGUÊS")
    print("=" * 100)
    
    total_errors = 0
    files_with_errors = []
    
    for filename in main_files:
        file_path = templates_dir / filename
        
        if not file_path.exists():
            continue
        
        print(f"\n📄 Verificando: {filename}")
        print("-" * 100)
        
        errors = check_portuguese_errors(file_path)
        
        if errors:
            total_errors += len(errors)
            files_with_errors.append(filename)
            
            for error in errors[:10]:  # Mostrar apenas primeiros 10 erros
                print(f"  ❌ Linha {error['line']:4d}: {error['reason']}")
                print(f"     Padrão: '{error['pattern']}'")
                print(f"     Correção sugerida: '{error['correction']}'")
                print(f"     Texto: {error['text']}")
                print()
            
            if len(errors) > 10:
                print(f"  ⚠️  ... e mais {len(errors) - 10} erros")
        else:
            print(f"  ✅ Nenhum erro encontrado!")
    
    print("\n" + "=" * 100)
    print("📊 RESUMO:")
    print("=" * 100)
    print(f"Total de erros encontrados: {total_errors}")
    print(f"Arquivos com erros: {len(files_with_errors)}")
    
    if files_with_errors:
        print("\n⚠️  Arquivos que precisam de correção:")
        for filename in files_with_errors:
            print(f"  • {filename}")
    else:
        print("\n✅ SUCESSO! Nenhum erro de português encontrado!")
    
    print("\n" + "=" * 100)

if __name__ == '__main__':
    main()
