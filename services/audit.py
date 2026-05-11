"""
Serviço de Auditoria - Registra todas as ações dos usuários no sistema
"""
import sqlite3
import os
from datetime import datetime, timezone, timedelta
from flask import request, session
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'ippel_system.db')

# Fuso horário de Brasília (UTC-3)
BRASILIA_TZ = timezone(timedelta(hours=-3))

def get_brasilia_time():
    """Retorna a data/hora atual no fuso de Brasília"""
    return datetime.now(BRASILIA_TZ).strftime('%Y-%m-%d %H:%M:%S')

# Tipos de eventos
EVENT_TYPES = {
    'LOGIN': 'Login no sistema',
    'LOGOUT': 'Logout do sistema',
    'SESSION_EXPIRED': 'Sessão expirada',
    'RNC_VIEW': 'Visualizou RNC',
    'RNC_CREATE': 'Criou RNC',
    'RNC_REPLY': 'Respondeu RNC',
    'RNC_UPDATE': 'Atualizou RNC',
    'RNC_DELETE': 'Excluiu RNC',
    'RNC_FINALIZE': 'Finalizou RNC',
    'RNC_SHARE': 'Compartilhou RNC',
    'RNC_PRINT': 'Imprimiu RNC',
    'RO_VIEW': 'Visualizou R.O',
    'RO_CREATE': 'Criou R.O',
    'RO_UPDATE': 'Atualizou R.O',
    'RO_DELETE': 'Excluiu R.O',
    'RO_FINALIZE': 'Finalizou R.O',
    'REPORT_GENERATE': 'Gerou relatório',
    'REPORT_VIEW': 'Visualizou relatório',
    'CHAT_MESSAGE': 'Enviou mensagem no chat',
    'CHAT_VIEW': 'Visualizou chat',
    'USER_CREATE': 'Criou usuário',
    'USER_UPDATE': 'Atualizou usuário',
    'USER_DELETE': 'Excluiu usuário',
    'PERMISSION_CHANGE': 'Alterou permissões',
    'REPORT_GENERATE': 'Gerou relatório',
    'EXPORT_DATA': 'Exportou dados',
    'PAGE_ACCESS': 'Acessou página',
}


def init_audit_table():
    """Cria a tabela de auditoria se não existir"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_description TEXT,
                user_id INTEGER,
                user_name TEXT,
                user_department TEXT,
                ip_address TEXT,
                user_agent TEXT,
                target_type TEXT,
                target_id INTEGER,
                target_name TEXT,
                details TEXT,
                old_value TEXT,
                new_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Índices para consultas rápidas
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_logs(event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_date ON audit_logs(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_logs(target_type, target_id)')
        
        conn.commit()
        conn.close()
        logger.info("Tabela audit_logs criada/verificada com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar tabela audit_logs: {e}")
        return False


def log_event(event_type, description=None, target_type=None, target_id=None, 
              target_name=None, details=None, old_value=None, new_value=None,
              user_id=None, user_name=None, ip_address=None, user_agent=None):
    """
    Registra um evento no log de auditoria
    
    Args:
        event_type: Tipo do evento (ver EVENT_TYPES)
        description: Descrição adicional do evento
        target_type: Tipo do objeto afetado (RNC, USER, etc)
        target_id: ID do objeto afetado
        target_name: Nome/identificador do objeto
        details: Detalhes adicionais (JSON string ou texto)
        old_value: Valor anterior (para alterações)
        new_value: Novo valor (para alterações)
        user_id: ID do usuário (se não informado, pega da sessão)
        user_name: Nome do usuário (se não informado, pega da sessão)
        ip_address: Endereço IP (se não informado, tenta pegar do request)
        user_agent: User-Agent do navegador
    """
    try:
        # Pegar dados do usuário da sessão se não fornecidos
        if user_id is None:
            try:
                user_id = session.get('user_id')
            except:
                pass
        if user_name is None:
            try:
                user_name = session.get('user_name')
            except:
                pass
        
        user_department = None
        try:
            user_department = session.get('user_department', '')
        except:
            pass
        
        # Pegar IP e User-Agent do request se não fornecidos
        if ip_address is None:
            try:
                ip_address = request.remote_addr
            except:
                pass
        if user_agent is None:
            try:
                user_agent = request.headers.get('User-Agent', '')[:500]
            except:
                pass
        
        # Descrição padrão se não fornecida
        if description is None:
            description = EVENT_TYPES.get(event_type, event_type)
        
        conn = sqlite3.connect(DB_PATH, timeout=30)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_logs 
            (event_type, event_description, user_id, user_name, user_department,
             ip_address, user_agent, target_type, target_id, target_name,
             details, old_value, new_value, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_type, description, user_id, user_name, user_department,
            ip_address, user_agent, target_type, target_id, target_name,
            details, old_value, new_value, get_brasilia_time()
        ))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Evento registrado: {event_type} - User: {user_name} - Target: {target_type}:{target_id}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao registrar evento de auditoria: {e}")
        return False


def log_login(user_id, user_name, ip_address=None, user_agent=None, success=True):
    """Registra tentativa de login"""
    event_type = 'LOGIN' if success else 'LOGIN_FAILED'
    description = f"Login {'bem-sucedido' if success else 'falhou'}"
    return log_event(event_type, description, user_id=user_id, user_name=user_name, 
                     ip_address=ip_address, user_agent=user_agent)


def log_logout(user_id=None, user_name=None, ip_address=None):
    """Registra logout"""
    return log_event('LOGOUT', 'Usuário saiu do sistema', user_id=user_id, user_name=user_name,
                     ip_address=ip_address)


def log_rnc_action(user_id, user_name, action, rnc_id, ip_address=None, details=None, old_value=None, new_value=None):
    """Registra ação em RNC"""
    event_type = action.upper() if action.startswith('RNC_') else f'RNC_{action.upper()}'
    description = f"{EVENT_TYPES.get(event_type, action)} - RNC #{rnc_id}"
    return log_event(
        event_type, description, 
        target_type='RNC', target_id=rnc_id,
        details=details, old_value=old_value, new_value=new_value,
        user_id=user_id, user_name=user_name, ip_address=ip_address
    )


def log_chat_message(rnc_id, message_preview=None):
    """Registra mensagem no chat"""
    # Limitar preview da mensagem por privacidade
    preview = message_preview[:100] + '...' if message_preview and len(message_preview) > 100 else message_preview
    return log_event(
        'CHAT_MESSAGE', 'Enviou mensagem no chat',
        target_type='RNC', target_id=rnc_id,
        details=preview
    )


def log_page_access(page_name, page_url=None):
    """Registra acesso a página"""
    return log_event(
        'PAGE_ACCESS', f'Acessou: {page_name}',
        details=page_url or request.path if request else None
    )


def get_audit_logs(filters=None, page=1, per_page=50):
    """
    Busca logs de auditoria com filtros
    
    Args:
        filters: dict com filtros (user_id, event_type, date_from, date_to, target_type)
        page: página atual
        per_page: itens por página
    
    Returns:
        dict com logs, total, páginas
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        where = ["1=1"]
        params = []
        
        if filters:
            if filters.get('user_id'):
                where.append("user_id = ?")
                params.append(filters['user_id'])
            
            if filters.get('user_name'):
                where.append("user_name LIKE ?")
                params.append(f"%{filters['user_name']}%")
            
            if filters.get('event_type'):
                where.append("event_type = ?")
                params.append(filters['event_type'])
            
            if filters.get('target_type'):
                where.append("target_type = ?")
                params.append(filters['target_type'])
            
            if filters.get('target_id'):
                where.append("target_id = ?")
                params.append(filters['target_id'])
            
            if filters.get('date_from'):
                where.append("date(created_at) >= date(?)")
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                where.append("date(created_at) <= date(?)")
                params.append(filters['date_to'])
            
            if filters.get('search'):
                where.append("(event_description LIKE ? OR details LIKE ? OR target_name LIKE ?)")
                search = f"%{filters['search']}%"
                params.extend([search, search, search])
        
        where_clause = " AND ".join(where)
        
        # Contar total
        cursor.execute(f"SELECT COUNT(*) FROM audit_logs WHERE {where_clause}", params)
        total = cursor.fetchone()[0]
        
        # Buscar logs com paginação
        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT * FROM audit_logs 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])
        
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            'logs': logs,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar logs de auditoria: {e}")
        return {'logs': [], 'total': 0, 'page': 1, 'per_page': per_page, 'pages': 0}


def get_user_activity(user_id, limit=100):
    """Busca atividade recente de um usuário específico"""
    return get_audit_logs(filters={'user_id': user_id}, per_page=limit)


def get_rnc_history(rnc_id):
    """Busca histórico completo de uma RNC"""
    return get_audit_logs(filters={'target_type': 'RNC', 'target_id': rnc_id}, per_page=1000)


# Inicializar tabela ao importar módulo
init_audit_table()
