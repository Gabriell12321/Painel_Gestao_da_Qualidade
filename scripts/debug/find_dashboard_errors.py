#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para identificar e corrigir erros de português no dashboard.html
"""

import re

def find_portuguese_errors(file_path):
    """Encontra possíveis erros de português em arquivo HTML"""
    
    errors = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Padrões de erros comuns
    patterns = [
        (r'Concluídos', 'Concluídos'),  # Verificar se está correto
        (r'Nenhum RNC', 'Nenhuma RNC'),  # RNC é feminino
        (r'Novo RNC', 'Nova RNC'),
        (r'Criar Novo RNC', 'Criar Nova RNC'),
        (r'o RNC', 'a RNC'),
        (r'Confirmar Deletar', 'Confirmar Exclusão'),
        (r'Deletar', 'Excluir'),
        (r'deletar', 'excluir'),
        (r'Análise', 'Análise'),  # verificar encoding
    ]
    
    print("=" * 100)
    print("🔍 PROCURANDO ERROS DE PORTUGUÊS NO DASHBOARD")
    print("=" * 100)
    
    # Buscar todas as strings visíveis (entre > e <, ou em atributos)
    visible_text_pattern = r'>([^<>]+)<'
    matches = re.finditer(visible_text_pattern, content)
    
    portuguese_texts = []
    for match in matches:
        text = match.group(1).strip()
        if text and not text.startswith(('var ', 'function', 'const ', 'let ', '//', '/*', '{', '}')):
            # Verificar se contém texto português
            if any(word in text.lower() for word in ['rnc', 'criar', 'novo', 'nenhum', 'deletar', 'excluir', 'confirmar', 'cancelar', 'finalizar', 'análise', 'dados', 'status', 'total', 'pendente', 'concluído', 'ações', 'atualizar', 'sair', 'gerenciar', 'usuário', 'cadastro', 'cliente']):
                portuguese_texts.append(text)
    
    # Remover duplicatas e ordenar
    portuguese_texts = sorted(set(portuguese_texts))
    
    print("\n📝 TEXTOS EM PORTUGUÊS ENCONTRADOS:")
    print("-" * 100)
    for i, text in enumerate(portuguese_texts, 1):
        # Verificar se tem erro
        has_error = False
        error_type = ""
        
        # RNC é feminino
        if re.search(r'\bo\s+RNC\b', text, re.IGNORECASE):
            has_error = True
            error_type = "❌ 'o RNC' → 'a RNC' (RNC é feminino)"
        elif re.search(r'\bNovo\s+RNC\b', text, re.IGNORECASE):
            has_error = True
            error_type = "❌ 'Novo RNC' → 'Nova RNC'"
        elif re.search(r'\bNenhum\s+RNC\b', text, re.IGNORECASE):
            has_error = True
            error_type = "❌ 'Nenhum RNC' → 'Nenhuma RNC'"
        elif re.search(r'\bdeletar\b', text, re.IGNORECASE):
            has_error = True
            error_type = "⚠️  'deletar' → 'excluir' (forma mais correta)"
        elif re.search(r'\bDeletar\b', text):
            has_error = True
            error_type = "⚠️  'Deletar' → 'Excluir'"
        
        status = error_type if has_error else "✅"
        print(f"{i:3d}. {status:50s} | {text}")
    
    print("\n" + "=" * 100)
    print(f"Total de textos encontrados: {len(portuguese_texts)}")
    
    return portuguese_texts

if __name__ == '__main__':
    file_path = 'templates/dashboard.html'
    find_portuguese_errors(file_path)
