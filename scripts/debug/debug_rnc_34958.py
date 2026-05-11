import sqlite3

DB_PATH = r'y:\rnc hml\ippel_system.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("=== RNC 34958 - Verificação completa ===\n")

# Buscar todos os campos relevantes
c.execute('''
    SELECT rnc_number, created_at, responsavel, price, status, 
           title, description, setor, area_responsavel
    FROM rncs 
    WHERE rnc_number = "34958"
''')

row = c.fetchone()
if row:
    print(f"RNC: {row[0]}")
    print(f"Data: {row[1]}")
    print(f"Responsável: {row[2]}")
    print(f"Valor (price): {row[3]}")
    print(f"Status: {row[4]}")
    print(f"Título: {row[5]}")
    print(f"Setor: {row[7]}")
    print(f"Área Responsável: {row[8]}")
else:
    print("RNC não encontrada")

# Buscar outras RNCs com mesmo responsável no mesmo período
print("\n=== Outras RNCs de Daiane em 13/06/2024 ===")
c.execute('''
    SELECT rnc_number, created_at, price, status
    FROM rncs
    WHERE created_at = "13/06/2024"
    AND (responsavel LIKE "%Daiane%" OR responsavel = "61")
    AND is_deleted = 0
''')

rows = c.fetchall()
if rows:
    total_valor = 0
    for row in rows:
        print(f"RNC-{row[0]}: price={row[2]}, status={row[3]}")
        try:
            if row[2]:
                valor = float(str(row[2]).replace('R$', '').replace(',', '.').strip())
                total_valor += valor
        except:
            pass
    print(f"\nTotal somado: R$ {total_valor}")
else:
    print("Nenhuma RNC encontrada")

conn.close()
