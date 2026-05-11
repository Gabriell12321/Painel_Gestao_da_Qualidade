with open('rnc verificar dados..txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# Mostrar cabeçalhos
cols = lines[0].split('\t')
print("Colunas do arquivo:")
for i, col in enumerate(cols):
    print(f"{i}: {col.strip()[:50]}")
    
print(f"\nTotal de colunas: {len(cols)}")

# Mostrar exemplo da segunda linha
print("\nSegunda linha (dados):")
data_cols = lines[1].split('\t')
for i in range(min(15, len(data_cols))):
    print(f"{i}: {data_cols[i].strip()[:50]}")
