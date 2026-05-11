import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

print("=== VERIFICANDO AGRUPAMENTO NO TEMPLATE ===\n")

# Simular o que o template vai fazer
cursor.execute("""
SELECT 
    COALESCE(u.name, r.responsavel) as responsavel,
    COALESCE(g.name, r.area_responsavel, r.setor, 'Não informado') as department,
    r.price,
    r.rnc_number
FROM rncs r
LEFT JOIN groups g ON (
    CAST(r.area_responsavel AS TEXT) = CAST(g.id AS TEXT) OR
    CAST(r.setor AS TEXT) = CAST(g.id AS TEXT)
)
LEFT JOIN users u ON CAST(r.responsavel AS TEXT) = CAST(u.id AS TEXT)
WHERE r.is_deleted = 0 
AND strftime('%Y-%m', r.created_at) = '2025-10'
AND r.status IN ('Finalizado', 'Pendente')
AND r.responsavel IS NOT NULL
AND r.responsavel != ''
ORDER BY department, responsavel
""")

print("Agrupamento por departamento:")
print("-" * 100)

current_dept = None
dept_total = 0
dept_employees = {}

for row in cursor.fetchall():
    responsavel = row[0]
    department = row[1]
    price = row[2]
    rnc = row[3]
    
    # Converter price para float
    try:
        if price:
            price_clean = str(price).replace('R$', '').replace(' ', '').replace(',', '').replace('"', '').replace("'", '')
            price_val = float(price_clean) if price_clean and price_clean != '0' else 0.0
        else:
            price_val = 0.0
    except:
        price_val = 0.0
    
    # Novo departamento
    if department != current_dept:
        # Imprimir totais do departamento anterior
        if current_dept:
            print(f"\n  Subtotal {current_dept}: R$ {dept_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            for emp, val in sorted(dept_employees.items()):
                print(f"    - {emp}: R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        # Resetar para novo departamento
        current_dept = department
        dept_total = 0
        dept_employees = {}
        print(f"\n{'='*100}")
        print(f"DEPARTAMENTO: {department}")
        print(f"{'='*100}")
    
    # Acumular valores
    dept_total += price_val
    if responsavel not in dept_employees:
        dept_employees[responsavel] = 0
    dept_employees[responsavel] += price_val

# Imprimir último departamento
if current_dept:
    print(f"\n  Subtotal {current_dept}: R$ {dept_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    for emp, val in sorted(dept_employees.items()):
        if val > 0:
            print(f"    - {emp}: R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

conn.close()
