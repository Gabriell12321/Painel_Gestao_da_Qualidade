"""
Rotas de Auditoria/Histórico - Apenas para administradores
"""
from flask import Blueprint, render_template, request, jsonify, session
from functools import wraps
import logging

logger = logging.getLogger(__name__)

audit_bp = Blueprint('audit', __name__)


def admin_required(f):
    """Decorator para verificar acesso de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Não autenticado'}), 401
        
        from services.permissions import has_permission
        if not has_permission(session['user_id'], 'admin_access'):
            return jsonify({'success': False, 'message': 'Acesso negado. Apenas administradores.'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


@audit_bp.route('/admin/history')
@admin_required
def history_page():
    """Página principal de histórico/auditoria"""
    from services.audit import get_audit_logs, EVENT_TYPES

    # Parâmetros de filtro
    page = request.args.get('page', 1, type=int)
    user_name = request.args.get('user', '')
    event_type = request.args.get('event', '')
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')
    search = request.args.get('search', '')
    target_type = request.args.get('target', '')

    # LOG DE DEBUG para verificar filtros
    logger.info(f"Filtros recebidos: user={user_name}, event={event_type}, from={date_from}, to={date_to}, search={search}, target={target_type}")

    filters = {}
    if user_name:
        filters['user_name'] = user_name
    if event_type:
        filters['event_type'] = event_type
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    if search:
        filters['search'] = search
    if target_type:
        filters['target_type'] = target_type

    result = get_audit_logs(filters=filters, page=page, per_page=50)

    logger.info(f"Resultado: {result['total']} registros encontrados, página {result['page']} de {result['pages']}")

    return render_template('admin_history.html',
        logs=result['logs'],
        total=result['total'],
        page=result['page'],
        pages=result['pages'],
        event_types=EVENT_TYPES,
        filters={
            'user': user_name,
            'event': event_type,
            'from': date_from,
            'to': date_to,
            'search': search,
            'target': target_type
        }
    )


@audit_bp.route('/api/audit/logs')
@admin_required
def api_get_logs():
    """API para buscar logs de auditoria"""
    from services.audit import get_audit_logs
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    filters = {}
    for key in ['user_id', 'user_name', 'event_type', 'target_type', 'target_id', 'date_from', 'date_to', 'search']:
        value = request.args.get(key)
        if value:
            filters[key] = value
    
    result = get_audit_logs(filters=filters, page=page, per_page=per_page)
    return jsonify({'success': True, **result})


@audit_bp.route('/api/audit/user/<int:user_id>')
@admin_required
def api_user_activity(user_id):
    """API para buscar atividade de um usuário específico"""
    from services.audit import get_user_activity
    
    limit = request.args.get('limit', 100, type=int)
    result = get_user_activity(user_id, limit=limit)
    return jsonify({'success': True, **result})


@audit_bp.route('/api/audit/rnc/<int:rnc_id>')
@admin_required
def api_rnc_history(rnc_id):
    """API para buscar histórico de uma RNC específica"""
    from services.audit import get_rnc_history
    
    result = get_rnc_history(rnc_id)
    return jsonify({'success': True, **result})


@audit_bp.route('/api/audit/stats')
@admin_required
def api_audit_stats():
    """API para estatísticas de auditoria"""
    import sqlite3
    import os
    
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'ippel_system.db')
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total de eventos
        cursor.execute('SELECT COUNT(*) FROM audit_logs')
        total_events = cursor.fetchone()[0]
        
        # Eventos hoje
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE date(created_at) = date('now')")
        events_today = cursor.fetchone()[0]
        
        # Logins hoje
        cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE event_type = 'LOGIN' AND date(created_at) = date('now')")
        logins_today = cursor.fetchone()[0]
        
        # Usuários ativos hoje
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM audit_logs WHERE date(created_at) = date('now')")
        active_users_today = cursor.fetchone()[0]
        
        # Top eventos
        cursor.execute('''
            SELECT event_type, COUNT(*) as count 
            FROM audit_logs 
            GROUP BY event_type 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        top_events = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Top usuários ativos
        cursor.execute('''
            SELECT user_name, COUNT(*) as count 
            FROM audit_logs 
            WHERE user_name IS NOT NULL
            GROUP BY user_id 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        top_users = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_events': total_events,
                'events_today': events_today,
                'logins_today': logins_today,
                'active_users_today': active_users_today,
                'top_events': top_events,
                'top_users': top_users
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas de auditoria: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
