#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🛡️ IPPEL Advanced Security Routes
Rotas de segurança avançadas para o sistema RNC IPPEL
"""

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from security_enhancements import SecurityManager, InputValidator, require_auth, require_permission, require_csrf, check_ip_blacklist, add_security_headers
from two_factor_auth import TwoFactorAuth, require_2fa
import sqlite3
import json
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash

# Blueprint para rotas de segurança
security_bp = Blueprint('security', __name__, url_prefix='/security')

# Instâncias globais
security_manager = None
tfa_system = None

def init_security_routes(app):
    """Inicializar rotas de segurança"""
    global security_manager, tfa_system
    
    security_manager = SecurityManager(app)
    tfa_system = TwoFactorAuth()
    
    # Registrar blueprint
    app.register_blueprint(security_bp)
    
    # Adicionar middleware de segurança
    @app.before_request
    def security_middleware():
        # Adicionar manager ao contexto global
        from flask import g
        g.security_manager = security_manager
        
        # Verificar blacklist de IP
        if security_manager.is_ip_blacklisted(security_manager.get_client_ip()):
            return jsonify({'error': 'Acesso negado'}), 403
    
    @app.after_request
    def add_security_headers_middleware(response):
        return add_security_headers(response)

@security_bp.route('/login', methods=['POST'])
@check_ip_blacklist
def enhanced_login():
    """Login com verificações de segurança aprimoradas"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validar entrada
        if not InputValidator.validate_email(email):
            return jsonify({'error': 'Email inválido'}), 400
        
        if not password:
            return jsonify({'error': 'Senha é obrigatória'}), 400
        
        ip_address = security_manager.get_client_ip()
        
        # Verificar tentativas de login
        attempts_info = security_manager.check_login_attempts(ip_address, email)
        
        if attempts_info['is_locked']:
            remaining_minutes = int(attempts_info['lockout_remaining'] / 60)
            security_manager.log_security_event('LOGIN_BLOCKED', {
                'email': email,
                'ip_address': ip_address,
                'reason': 'Too many failed attempts',
                'remaining_minutes': remaining_minutes
            }, 'HIGH')
            
            return jsonify({
                'error': f'Conta bloqueada. Tente novamente em {remaining_minutes} minutos.',
                'locked_until': remaining_minutes
            }), 429
        
        # Verificar credenciais no banco
        with sqlite3.connect('ippel_system.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, password_hash, name, two_factor_enabled 
                FROM users WHERE email = ? AND is_active = 1
            ''', (email,))
            
            user = cursor.fetchone()
            
            if not user or not check_password_hash(user[1], password):
                # Registrar tentativa falhada
                security_manager.record_login_attempt(ip_address, email, False)
                security_manager.log_security_event('LOGIN_FAILED', {
                    'email': email,
                    'ip_address': ip_address,
                    'reason': 'Invalid credentials'
                }, 'MEDIUM')
                
                return jsonify({'error': 'Credenciais inválidas'}), 401
            
            user_id, password_hash, name, two_factor_enabled = user
            
            # Registrar tentativa bem-sucedida
            security_manager.record_login_attempt(ip_address, email, True)
            
            # Se 2FA está habilitado, não fazer login completo ainda
            if two_factor_enabled:
                # Criar sessão temporária para 2FA
                session['pending_2fa_user_id'] = user_id
                session['pending_2fa_email'] = email
                session['pending_2fa_time'] = datetime.now().isoformat()
                
                security_manager.log_security_event('2FA_REQUIRED', {
                    'user_id': user_id,
                    'email': email,
                    'ip_address': ip_address
                })
                
                return jsonify({
                    'success': True,
                    'requires_2fa': True,
                    'message': 'Digite o código do seu autenticador'
                }), 200
            
            # Login normal sem 2FA
            session_token = security_manager.create_secure_session(user_id)
            
            if not session_token:
                return jsonify({'error': 'Erro interno do servidor'}), 500
            
            security_manager.log_security_event('LOGIN_SUCCESS', {
                'user_id': user_id,
                'email': email,
                'ip_address': ip_address,
                'session_token': session_token[:16] + '...'
            })
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user_id,
                    'name': name,
                    'email': email
                },
                'message': 'Login realizado com sucesso'
            }), 200
    
    except Exception as e:
        security_manager.log_security_event('LOGIN_ERROR', {
            'error': str(e),
            'ip_address': security_manager.get_client_ip()
        }, 'HIGH')
        
        return jsonify({'error': 'Erro interno do servidor'}), 500

@security_bp.route('/verify-2fa', methods=['POST'])
@check_ip_blacklist
def verify_2fa():
    """Verificar código 2FA"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'error': 'Token é obrigatório'}), 400
        
        # Verificar se há sessão 2FA pendente
        if 'pending_2fa_user_id' not in session:
            return jsonify({'error': 'Nenhuma verificação 2FA pendente'}), 400
        
        user_id = session['pending_2fa_user_id']
        email = session['pending_2fa_email']
        pending_time = datetime.fromisoformat(session['pending_2fa_time'])
        
        # Verificar timeout (5 minutos)
        if (datetime.now() - pending_time).total_seconds() > 300:
            session.pop('pending_2fa_user_id', None)
            session.pop('pending_2fa_email', None)
            session.pop('pending_2fa_time', None)
            
            return jsonify({'error': 'Tempo para verificação 2FA expirado'}), 408
        
        # Verificar token 2FA
        result = tfa_system.verify_2fa_token(user_id, token)
        
        if not result['success']:
            security_manager.log_security_event('2FA_FAILED', {
                'user_id': user_id,
                'email': email,
                'ip_address': security_manager.get_client_ip(),
                'error': result.get('error')
            }, 'MEDIUM')
            
            return jsonify({'error': result['error']}), 401
        
        # 2FA verificado com sucesso - criar sessão completa
        session_token = security_manager.create_secure_session(user_id)
        session['2fa_verified'] = True
        
        # Limpar dados temporários
        session.pop('pending_2fa_user_id', None)
        session.pop('pending_2fa_email', None)
        session.pop('pending_2fa_time', None)
        
        # Buscar dados do usuário
        with sqlite3.connect('ippel_system.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM users WHERE id = ?', (user_id,))
            user_name = cursor.fetchone()[0]
        
        security_manager.log_security_event('2FA_SUCCESS', {
            'user_id': user_id,
            'email': email,
            'ip_address': security_manager.get_client_ip(),
            'method': result['method']
        })
        
        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'name': user_name,
                'email': email
            },
            'message': 'Login realizado com sucesso'
        }), 200
    
    except Exception as e:
        security_manager.log_security_event('2FA_ERROR', {
            'error': str(e),
            'ip_address': security_manager.get_client_ip()
        }, 'HIGH')
        
        return jsonify({'error': 'Erro interno do servidor'}), 500

@security_bp.route('/setup-2fa', methods=['GET'])
@require_auth
def setup_2fa():
    """Configurar 2FA para o usuário"""
    try:
        user_id = session['user_id']
        
        # Buscar email do usuário
        with sqlite3.connect('ippel_system.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT email FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'error': 'Usuário não encontrado'}), 404
            
            user_email = result[0]
        
        # Configurar 2FA
        result = tfa_system.setup_2fa_for_user(user_id, user_email)
        
        if result['success']:
            security_manager.log_security_event('2FA_SETUP_INITIATED', {
                'user_id': user_id,
                'email': user_email
            })
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'Erro ao configurar 2FA: {str(e)}'}), 500

@security_bp.route('/enable-2fa', methods=['POST'])
@require_auth
@require_csrf
def enable_2fa():
    """Habilitar 2FA após verificação"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'error': 'Token é obrigatório'}), 400
        
        user_id = session['user_id']
        result = tfa_system.verify_and_enable_2fa(user_id, token)
        
        if result['success']:
            session['2fa_verified'] = True
            security_manager.log_security_event('2FA_ENABLED', {
                'user_id': user_id
            })
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'Erro ao habilitar 2FA: {str(e)}'}), 500

@security_bp.route('/disable-2fa', methods=['POST'])
@require_auth
@require_csrf
@require_2fa
def disable_2fa():
    """Desabilitar 2FA"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        if not password:
            return jsonify({'error': 'Senha é obrigatória para desabilitar 2FA'}), 400
        
        user_id = session['user_id']
        
        # Verificar senha atual
        with sqlite3.connect('ippel_system.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            
            if not result or not check_password_hash(result[0], password):
                return jsonify({'error': 'Senha incorreta'}), 401
        
        result = tfa_system.disable_2fa(user_id)
        
        if result['success']:
            session.pop('2fa_verified', None)
            security_manager.log_security_event('2FA_DISABLED', {
                'user_id': user_id
            }, 'MEDIUM')
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'Erro ao desabilitar 2FA: {str(e)}'}), 500

@security_bp.route('/regenerate-backup-codes', methods=['POST'])
@require_auth
@require_csrf
@require_2fa
def regenerate_backup_codes():
    """Regenerar códigos de backup"""
    try:
        user_id = session['user_id']
        result = tfa_system.regenerate_backup_codes(user_id)
        
        if result['success']:
            security_manager.log_security_event('BACKUP_CODES_REGENERATED', {
                'user_id': user_id
            })
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'Erro ao regenerar códigos: {str(e)}'}), 500

@security_bp.route('/change-password', methods=['POST'])
@require_auth
@require_csrf
def change_password():
    """Alterar senha com validações de segurança"""
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'Nova senha e confirmação não coincidem'}), 400
        
        user_id = session['user_id']
        
        # Verificar senha atual
        with sqlite3.connect('ippel_system.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash, email FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            
            if not result or not check_password_hash(result[0], current_password):
                security_manager.log_security_event('PASSWORD_CHANGE_FAILED', {
                    'user_id': user_id,
                    'reason': 'Invalid current password'
                }, 'MEDIUM')
                return jsonify({'error': 'Senha atual incorreta'}), 401
            
            email = result[1]
        
        # Validar força da nova senha
        validation = security_manager.validate_password_strength(new_password)
        
        if not validation['is_valid']:
            return jsonify({
                'error': 'Senha não atende aos critérios de segurança',
                'issues': validation['issues']
            }), 400
        
        # Atualizar senha
        new_password_hash = generate_password_hash(new_password)
        
        with sqlite3.connect('ippel_system.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET password_hash = ? WHERE id = ?
            ''', (new_password_hash, user_id))
            conn.commit()
        
        security_manager.log_security_event('PASSWORD_CHANGED', {
            'user_id': user_id,
            'email': email,
            'strength': validation['strength']
        })
        
        return jsonify({
            'success': True,
            'message': 'Senha alterada com sucesso',
            'strength': validation['strength']
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro ao alterar senha: {str(e)}'}), 500

@security_bp.route('/security-audit', methods=['GET'])
@require_auth
@require_permission('manage_users')
def security_audit():
    """Relatório de auditoria de segurança"""
    try:
        user_id = request.args.get('user_id', type=int)
        days = request.args.get('days', 7, type=int)
        risk_level = request.args.get('risk_level', 'ALL')
        
        with sqlite3.connect('ippel_system.db') as conn:
            cursor = conn.cursor()
            
            # Query base
            query = '''
                SELECT a.*, u.name, u.email 
                FROM audit_log a
                LEFT JOIN users u ON a.user_id = u.id
                WHERE a.timestamp > datetime('now', '-{} days')
            '''.format(days)
            
            params = []
            
            if user_id:
                query += ' AND a.user_id = ?'
                params.append(user_id)
            
            if risk_level != 'ALL':
                query += ' AND a.risk_level = ?'
                params.append(risk_level)
            
            query += ' ORDER BY a.timestamp DESC LIMIT 1000'
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Estatísticas
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_events,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT ip_address) as unique_ips,
                    SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_risk,
                    SUM(CASE WHEN risk_level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_risk
                FROM audit_log 
                WHERE timestamp > datetime('now', '-{} days')
            '''.format(days), params[:1] if user_id else [])
            
            stats = cursor.fetchone()
            
            # Top IPs
            cursor.execute('''
                SELECT ip_address, COUNT(*) as event_count
                FROM audit_log 
                WHERE timestamp > datetime('now', '-{} days')
                GROUP BY ip_address 
                ORDER BY event_count DESC 
                LIMIT 10
            '''.format(days))
            
            top_ips = cursor.fetchall()
        
        return jsonify({
            'events': [
                {
                    'id': row[0],
                    'user_id': row[1],
                    'action': row[2],
                    'resource': row[3],
                    'details': json.loads(row[4]) if row[4] else {},
                    'ip_address': row[5],
                    'user_agent': row[6],
                    'timestamp': row[7],
                    'risk_level': row[8],
                    'user_name': row[9],
                    'user_email': row[10]
                }
                for row in results
            ],
            'statistics': {
                'total_events': stats[0],
                'unique_users': stats[1],
                'unique_ips': stats[2],
                'high_risk_events': stats[3],
                'critical_risk_events': stats[4]
            },
            'top_ips': [
                {'ip': ip, 'count': count} for ip, count in top_ips
            ]
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar relatório: {str(e)}'}), 500

@security_bp.route('/active-sessions', methods=['GET'])
@require_auth
def get_active_sessions():
    """Listar sessões ativas do usuário"""
    try:
        user_id = session['user_id']
        
        with sqlite3.connect('ippel_system.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, ip_address, user_agent, created_at, last_activity, session_token
                FROM active_sessions 
                WHERE user_id = ? AND is_active = 1
                ORDER BY last_activity DESC
            ''', (user_id,))
            
            sessions = cursor.fetchall()
            current_session = session.get('session_token')
        
        return jsonify({
            'sessions': [
                {
                    'id': s[0],
                    'ip_address': s[1],
                    'user_agent': s[2],
                    'created_at': s[3],
                    'last_activity': s[4],
                    'is_current': s[5] == current_session
                }
                for s in sessions
            ]
        })
    
    except Exception as e:
        return jsonify({'error': f'Erro ao listar sessões: {str(e)}'}), 500

@security_bp.route('/revoke-session/<int:session_id>', methods=['POST'])
@require_auth
@require_csrf
def revoke_session(session_id):
    """Revogar sessão específica"""
    try:
        user_id = session['user_id']
        
        with sqlite3.connect('ippel_system.db') as conn:
            cursor = conn.cursor()
            
            # Verificar se a sessão pertence ao usuário
            cursor.execute('''
                SELECT session_token FROM active_sessions 
                WHERE id = ? AND user_id = ?
            ''', (session_id, user_id))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Sessão não encontrada'}), 404
            
            # Não permitir revogar a sessão atual
            if result[0] == session.get('session_token'):
                return jsonify({'error': 'Não é possível revogar a sessão atual'}), 400
            
            # Revogar sessão
            cursor.execute('''
                UPDATE active_sessions SET is_active = 0 
                WHERE id = ? AND user_id = ?
            ''', (session_id, user_id))
            
            conn.commit()
        
        security_manager.log_security_event('SESSION_REVOKED', {
            'user_id': user_id,
            'revoked_session_id': session_id
        })
        
        return jsonify({'success': True, 'message': 'Sessão revogada com sucesso'})
    
    except Exception as e:
        return jsonify({'error': f'Erro ao revogar sessão: {str(e)}'}), 500

@security_bp.route('/csrf-token', methods=['GET'])
@require_auth
def get_csrf_token():
    """Obter token CSRF"""
    token = security_manager.generate_csrf_token()
    return jsonify({'csrf_token': token})

@security_bp.route('/logout', methods=['POST'])
@require_auth
def secure_logout():
    """Logout seguro"""
    try:
        user_id = session.get('user_id')
        session_token = session.get('session_token')
        
        if user_id and session_token:
            # Invalidar sessão no banco
            with sqlite3.connect('ippel_system.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE active_sessions SET is_active = 0 
                    WHERE user_id = ? AND session_token = ?
                ''', (user_id, session_token))
                conn.commit()
            
            security_manager.log_security_event('LOGOUT', {
                'user_id': user_id,
                'session_token': session_token[:16] + '...'
            })
        
        # Limpar sessão
        session.clear()
        
        return jsonify({'success': True, 'message': 'Logout realizado com sucesso'})
    
    except Exception as e:
        return jsonify({'error': f'Erro no logout: {str(e)}'}), 500
