import sqlite3

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

print("=== RESPONSÁVEIS COM NÚMEROS EM OUTUBRO ===")
cursor.execute("""
SELECT DISTINCT r.responsavel, COUNT(*) as qtd
FROM rncs r
WHERE r.is_deleted = 0 
AND strftime('%Y-%m', r.created_at) = '2025-10'
AND r.responsavel IS NOT NULL
AND r.responsavel != ''
AND CAST(r.responsavel AS TEXT) GLOB '[0-9]*'
GROUP BY r.responsavel
ORDER BY r.responsavel
""")

print("\nResponsável (ID) | Quantidade")
print("-" * 40)
for row in cursor.fetchall():
    print(f"{row[0]} | {row[1]} RNCs")

print("\n=== VERIFICANDO SE EXISTEM NA TABELA USERS ===")
cursor.execute("""
SELECT u.id, u.name, u.department
FROM users u
WHERE CAST(u.id AS TEXT) IN (
    SELECT DISTINCT r.responsavel
    FROM rncs r
    WHERE r.is_deleted = 0 
    AND strftime('%Y-%m', r.created_at) = '2025-10'
    AND CAST(r.responsavel AS TEXT) GLOB '[0-9]*'
)
ORDER BY u.name
""")

print("\nID | Nome | Departamento")
print("-" * 60)
for row in cursor.fetchall():
    print(f"{row[0]} | {row[1]} | {row[2]}")

conn.close()
