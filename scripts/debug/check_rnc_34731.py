import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Verificar RNC 34731 (a que está na imagem)
cursor.execute("""
    SELECT rnc_number, ass_responsavel, area_responsavel 
    FROM rncs 
    WHERE rnc_number = '34731'
""")
rnc = cursor.fetchone()

print("=" * 60)
print("RNC 34731 - CAMPO ASSINATURA RESPONSÁVEL")
print("=" * 60)
if rnc:
    print(f"RNC: {rnc[0]}")
    print(f"ass_responsavel: '{rnc[1]}'")
    print(f"area_responsavel: '{rnc[2]}'")
    
    # Se area_responsavel é '7' (Engenharia), buscar gerente
    if rnc[2] == '7':
        cursor.execute("""
            SELECT manager_user_id FROM groups WHERE id = 7
        """)
        manager_row = cursor.fetchone()
        if manager_row and manager_row[0]:
            cursor.execute("SELECT name FROM users WHERE id = ?", (manager_row[0],))
            manager = cursor.fetchone()
            print(f"\nGerente da Engenharia (esperado): {manager[0] if manager else 'N/A'}")
            print(f"Gerente salvo na RNC: '{rnc[1]}'")
            
            if not rnc[1] or rnc[1] == '':
                print("\n❌ PROBLEMA: Campo vazio no banco de dados!")
                print("   O JavaScript não está enviando o valor corretamente")
else:
    print("RNC não encontrada")

conn.close()
