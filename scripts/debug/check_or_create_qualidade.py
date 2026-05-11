import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Verificar se QUALIDADE já existe
cursor.execute("SELECT codigo, setor, descricao, valor_hora FROM valores_hora WHERE setor = 'QUALIDADE' ORDER BY codigo")
rows = cursor.fetchall()

if rows:
    print(f'Categoria QUALIDADE já existe com {len(rows)} itens:\n')
    for r in rows:
        print(f'  {r[0]} - {r[2]}: R$ {r[3]:.2f}/h')
else:
    print('Categoria QUALIDADE não encontrada. Criando...\n')
    
    # Buscar próximo código disponível
    cursor.execute("SELECT MAX(CAST(SUBSTR(codigo, 1, 2) AS INTEGER)) FROM valores_hora")
    max_code = cursor.fetchone()[0] or 1
    next_code = max_code + 1
    
    valores_qualidade = [
        (f'{next_code:02d}.01', 'QUALIDADE', 'Inspeção Visual', 45.00),
        (f'{next_code:02d}.02', 'QUALIDADE', 'Inspeção Dimensional', 50.00),
        (f'{next_code:02d}.03', 'QUALIDADE', 'Análise de Conformidade', 55.00),
        (f'{next_code:02d}.04', 'QUALIDADE', 'Controle de Qualidade', 48.00),
        (f'{next_code:02d}.05', 'QUALIDADE', 'Auditoria Interna', 60.00),
        (f'{next_code:02d}.06', 'QUALIDADE', 'Calibração de Instrumentos', 52.00),
    ]
    
    for codigo, setor, descricao, valor in valores_qualidade:
        cursor.execute("""
            INSERT INTO valores_hora (codigo, setor, descricao, valor_hora, created_at, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (codigo, setor, descricao, valor))
        print(f'✓ {codigo} - {descricao}: R$ {valor:.2f}/h')
    
    conn.commit()
    print(f'\n{len(valores_qualidade)} itens adicionados!')

conn.close()
