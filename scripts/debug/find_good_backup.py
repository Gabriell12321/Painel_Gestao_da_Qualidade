import sqlite3
import shutil

backups_to_test = [
    "ippel_system_backup_20251107_094908.db",
    "ippel_system_backup_20251107_093239.db",
    "ippel_system_backup_20251107_092711.db",
    "ippel_system_backup_20251107_092521.db",
    "ippel_system_backup_20251107_092042.db",
    "ippel_system_backup_20251107_085525.db",
]

print("="*80)
print("TESTANDO BACKUPS")
print("="*80)

for backup in backups_to_test:
    try:
        print(f"\nTestando: {backup}")
        conn = sqlite3.connect(backup)
        cursor = conn.cursor()
        
        # Teste de integridade
        cursor.execute('PRAGMA integrity_check')
        result = cursor.fetchone()[0]
        
        if result == 'ok':
            # Contar RNCs
            cursor.execute('SELECT COUNT(*) FROM rncs')
            rnc_count = cursor.fetchone()[0]
            
            # Contar usuários
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            
            print(f"  ✅ BACKUP BOM!")
            print(f"     RNCs: {rnc_count}")
            print(f"     Usuários: {user_count}")
            
            # Restaurar
            conn.close()
            print(f"\n  Restaurando {backup}...")
            shutil.copy(backup, 'ippel_system.db')
            print(f"  ✅ BANCO RESTAURADO!")
            break
        else:
            print(f"  ❌ Corrompido: {result[:100]}")
            conn.close()
            
    except Exception as e:
        print(f"  ❌ Erro: {str(e)[:100]}")

print("\n" + "="*80)
