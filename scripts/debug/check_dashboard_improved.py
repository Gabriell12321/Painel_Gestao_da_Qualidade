#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar erros de português no dashboard_improved.html
"""

import re

def check_file(file_path):
    """Verifica erros de português em um arquivo"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except:
        print(f"❌ Erro ao abrir arquivo: {file_path}")
        return
    
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
        (r'�', '[CARACTERE INVÁLIDO]', 'Problema de encoding'),
    ]
    
    print("=" * 100)
    print(f"🔍 VERIFICANDO: {file_path}")
    print("=" * 100)
    
    errors = []
    
    for line_num, line in enumerate(lines, 1):
        # Ignorar linhas de comentário
        if line.strip().startswith(('//','/*','*','<!--')):
            continue
            
        for pattern, correction, reason in patterns:
            matches = list(re.finditer(pattern, line, re.IGNORECASE))
            for match in matches:
                errors.append({
                    'line': line_num,
                    'col': match.start(),
                    'text': line.strip()[:120],
                    'match': match.group(),
                    'correction': correction,
                    'reason': reason
                })
    
    if errors:
        print(f"\n❌ ENCONTRADOS {len(errors)} ERROS:\n")
        
        for i, error in enumerate(errors, 1):
            print(f"{i}. Linha {error['line']:4d}, Coluna {error['col']:3d}")
            print(f"   Problema: {error['reason']}")
            print(f"   Encontrado: '{error['match']}'")
            print(f"   Correção: '{error['correction']}'")
            print(f"   Contexto: {error['text']}")
            print()
    else:
        print("\n✅ NENHUM ERRO ENCONTRADO!")
    
    print("=" * 100)
    print(f"Total de erros: {len(errors)}")
    print("=" * 100)

if __name__ == '__main__':
    check_file('templates/dashboard_improved.html')
