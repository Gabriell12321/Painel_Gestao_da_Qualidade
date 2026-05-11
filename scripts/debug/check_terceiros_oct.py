import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

print('=== VERIFICANDO RNCs DE TERCEIROS (OUTUBRO 2025) ===\n')

# Consulta ampla procurando por "terceiros" em várias colunas
cursor.execute("""
SELECT 
    r.rnc_number, 
    r.created_at, 
    r.area_responsavel, 
    r.setor, 
    r.responsavel,
    r.price,
    r.status
FROM rncs r
WHERE r.is_deleted = 0 
AND strftime('%Y-%m', r.created_at) = '2025-11'
AND (
    lower(r.area_responsavel) LIKE '%terceiro%' OR
    lower(r.setor) LIKE '%terceiro%' OR
    lower(r.responsavel) LIKE '%terceiro%'
)
ORDER BY r.created_at
""")

rows = cursor.fetchall()

if not rows:
    print('Nenhuma RNC de "Terceiros" encontrada em Outubro de 2025.')
else:
    print(f'Encontradas {len(rows)} RNCs de Terceiros:\n')
    print(f"{'RNC':<10} | {'Data':<12} | {'Área':<15} | {'Setor':<15} | {'Responsável':<20} | {'Valor':<10}")
    print("-" * 90)
    for r in rows:
        print(f"{r[0]:<10} | {r[1][:10]:<12} | {r[2] or '':<15} | {r[3] or '':<15} | {r[4] or '':<20} | {r[5]}")

conn.close()
