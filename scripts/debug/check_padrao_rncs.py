import sqlite3
from datetime import datetime

conn = sqlite3.connect('ippel_system.db')
cursor = conn.cursor()

# Ver padrão de números de RNC por data
cursor.execute("""
SELECT 
    DATE(created_at) as data,
    MIN(CAST(rnc_number AS INTEGER)) as min_rnc,
    MAX(CAST(rnc_number AS INTEGER)) as max_rnc,
    COUNT(*) as total
FROM rncs
WHERE is_deleted = 0
AND created_at >= '2025-10-01'
GROUP BY DATE(created_at)
ORDER BY DATE(created_at) DESC
LIMIT 20
""")

print('=== Padrão de RNCs por data ===\n')
for row in cursor.fetchall():
    print(f'{row[0]}: RNC {row[1]} até {row[2]} ({row[3]} RNCs)')

# Ver se há importações em massa
cursor.execute("""
SELECT 
    DATE(created_at) as data,
    COUNT(CASE WHEN CAST(rnc_number AS INTEGER) < 30000 THEN 1 END) as antigas,
    COUNT(CASE WHEN CAST(rnc_number AS INTEGER) >= 30000 THEN 1 END) as recentes
FROM rncs
WHERE is_deleted = 0
AND created_at >= '2025-10-01'
GROUP BY DATE(created_at)
HAVING antigas > 0
ORDER BY DATE(created_at) DESC
""")

print('\n=== Dias com importações de RNCs antigas ===\n')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]} antigas + {row[2]} recentes')

conn.close()
