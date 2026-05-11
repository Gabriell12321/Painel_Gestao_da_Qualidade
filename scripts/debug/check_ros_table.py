import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Verificar se tabela existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ros'")
result = cursor.fetchone()

if result:
    print("✓ Tabela 'ros' existe no banco de dados")
    
    # Verificar estrutura
    cursor.execute("PRAGMA table_info(ros)")
    columns = cursor.fetchall()
    print(f"\n📋 Estrutura da tabela 'ros' ({len(columns)} colunas):")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Contar registros
    cursor.execute("SELECT COUNT(*) FROM ros")
    count = cursor.fetchone()[0]
    print(f"\n📊 Total de registros: {count}")
else:
    print("✗ Tabela 'ros' NÃO existe no banco de dados")
    print("\n⚠️ A tabela será criada quando o servidor for iniciado")

conn.close()
