import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Buscar RNC 34733 (última criada)
cursor.execute("""
    SELECT 
        rnc_number,
        signature_inspection_name,
        ass_responsavel,
        causador_user_id,
        signature_inspection2_name
    FROM rncs 
    WHERE rnc_number = '34733'
""")
rnc = cursor.fetchone()

print("=" * 70)
print("RNC 34733 - DADOS DOS CAMPOS DE VISTO")
print("=" * 70)

if rnc:
    print(f"\n1. VISTO - Qualidade")
    print(f"   Campo: signature_inspection_name")
    print(f"   Valor: '{rnc[1]}'")
    
    print(f"\n2. VISTO - Gerente do Setor")
    print(f"   Campo: ass_responsavel")
    print(f"   Valor: '{rnc[2]}'")
    
    print(f"\n3. VISTO - Causador")
    print(f"   Campo: causador_name (ID: {rnc[3]})")
    if rnc[3]:
        cursor.execute("SELECT name FROM users WHERE id = ?", (rnc[3],))
        user = cursor.fetchone()
        print(f"   Valor: '{user[0] if user else 'N/A'}'")
    else:
        print(f"   Fallback: signature_inspection2_name = '{rnc[4]}'")
    
    print(f"\n{'=' * 70}")
    print("DIAGNÓSTICO:")
    print("=" * 70)
    
    if not rnc[2] or rnc[2] == '':
        print("⚠️ PROBLEMA: ass_responsavel está vazio!")
        print("   Solução: Recriar a RNC para preencher automaticamente")
    else:
        print("✓ ass_responsavel está preenchido corretamente")
else:
    print("RNC não encontrada")

conn.close()
