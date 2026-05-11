#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔐 IPPEL Security Enhancements
Sistema de segurança avançado para o sistema RNC IPPEL
"""

import hashlib
import hmac
import secrets
import time
import json
import sqlite3
import re
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, session, jsonify, abort, g
from werkzeug.security import check_password_hash, generate_password_hash
import ipaddress
from typing import Dict, List, Optional, Tuple, Any

# Configurações de segurança
SECURITY_CONFIG = {
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 1800,  # 30 minutos
    'SESSION_TIMEOUT': 28800,   # 8 horas
    'PASSWORD_MIN_LENGTH': 8,
    'PASSWORD_REQUIRE_SPECIAL': True,
    'PASSWORD_REQUIRE_NUMBERS': True,
    'PASSWORD_REQUIRE_UPPERCASE': True,
    'AUDIT_LOG_RETENTION_DAYS': 90,
    'SUSPICIOUS_ACTIVITY_THRESHOLD': 10,
    'IP_WHITELIST_ENABLED': False,
    'ALLOWED_IP_RANGES': ['192.168.0.0/16', '10.0.0.0/8', '172.16.0.0/12'],
    'JWT_SECRET_ROTATION_DAYS': 30,
    'ENCRYPT_SENSITIVE_DATA': True,
    'RATE_LIMIT_PER_IP': 100,  # requests per minute
    'BRUTE_FORCE_PROTECTION': True
}

class SecurityManager:
    """Gerenciador central de segurança"""
    
    def __init__(self, app, db_path='ippel_system.db'):
        self.app = app
        self.db_path = db_path
        self.setup_security_tables()
        self.setup_logging()
        
    def setup_logging(self):
        """Configurar logging de segurança"""
        security_logger = logging.getLogger('ippel_security')
        security_logger.setLevel(logging.INFO)
        
        # Handler para arquivo de segurança
        handler = logging.FileHandler('ippel_security.log', encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        security_logger.addHandler(handler)
        
        self.security_logger = security_logger
    
    def setup_security_tables(self):
        """Criar tabelas de segurança"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela de tentativas de login
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    email TEXT,
                    success BOOLEAN NOT NULL,
                    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_agent TEXT,
                    geolocation TEXT
                )
            ''')
            
            # Tabela de auditoria
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    resource TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    risk_level TEXT DEFAULT 'LOW'
                )
            ''')
            
            # Tabela de sessões ativas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Tabela de blacklist de IPs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ip_blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT UNIQUE NOT NULL,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tabela de configurações de segurança
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(attempt_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON active_sessions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON active_sessions(session_token)')
            
            conn.commit()
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], 
                          risk_level: str = 'LOW', user_id: Optional[int] = None):
        """Registrar evento de segurança"""
        try:
            ip_address = self.get_client_ip()
            user_agent = request.headers.get('User-Agent', '')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audit_log (user_id, action, resource, details, 
                                         ip_address, user_agent, risk_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, event_type, details.get('resource', ''), 
                     json.dumps(details), ip_address, user_agent, risk_level))
                conn.commit()
            
            # Log também no arquivo
            log_message = f"{event_type} - IP: {ip_address} - Details: {details}"
            if risk_level in ['HIGH', 'CRITICAL']:
                self.security_logger.warning(log_message)
            else:
                self.security_logger.info(log_message)
                
        except Exception as e:
            self.security_logger.error(f"Erro ao registrar evento de segurança: {e}")
    
    def get_client_ip(self) -> str:
        """Obter IP real do cliente"""
        # Verificar headers de proxy
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        elif request.headers.get('CF-Connecting-IP'):
            return request.headers.get('CF-Connecting-IP')
        else:
            return request.remote_addr or '127.0.0.1'
    
    def is_ip_blacklisted(self, ip_address: str) -> bool:
        """Verificar se IP está na blacklist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id FROM ip_blacklist 
                    WHERE ip_address = ? AND is_active = 1 
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ''', (ip_address,))
                return cursor.fetchone() is not None
        except Exception:
            return False
    
    def add_ip_to_blacklist(self, ip_address: str, reason: str, 
                           duration_minutes: Optional[int] = None):
        """Adicionar IP à blacklist"""
        try:
            expires_at = None
            if duration_minutes:
                expires_at = datetime.now() + timedelta(minutes=duration_minutes)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ip_blacklist 
                    (ip_address, reason, expires_at) VALUES (?, ?, ?)
                ''', (ip_address, reason, expires_at))
                conn.commit()
            
            self.log_security_event('IP_BLACKLISTED', {
                'ip_address': ip_address,
                'reason': reason,
                'duration_minutes': duration_minutes
            }, 'HIGH')
            
        except Exception as e:
            self.security_logger.error(f"Erro ao adicionar IP à blacklist: {e}")
    
    def check_login_attempts(self, ip_address: str, email: str = None) -> Dict[str, Any]:
        """Verificar tentativas de login"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Contar tentativas falhadas nas últimas 24 horas
                cursor.execute('''
                    SELECT COUNT(*) FROM login_attempts 
                    WHERE ip_address = ? AND success = 0 
                    AND attempt_time > datetime('now', '-24 hours')
                ''', (ip_address,))
                ip_attempts = cursor.fetchone()[0]
                
                email_attempts = 0
                if email:
                    cursor.execute('''
                        SELECT COUNT(*) FROM login_attempts 
                        WHERE email = ? AND success = 0 
                        AND attempt_time > datetime('now', '-24 hours')
                    ''', (email,))
                    email_attempts = cursor.fetchone()[0]
                
                # Verificar se está bloqueado
                cursor.execute('''
                    SELECT attempt_time FROM login_attempts 
                    WHERE ip_address = ? AND success = 0 
                    ORDER BY attempt_time DESC LIMIT 1
                ''', (ip_address,))
                last_attempt = cursor.fetchone()
                
                is_locked = False
                lockout_remaining = 0
                
                if (ip_attempts >= SECURITY_CONFIG['MAX_LOGIN_ATTEMPTS'] or 
                    email_attempts >= SECURITY_CONFIG['MAX_LOGIN_ATTEMPTS']):
                    
                    if last_attempt:
                        last_time = datetime.fromisoformat(last_attempt[0])
                        time_diff = (datetime.now() - last_time).total_seconds()
                        
                        if time_diff < SECURITY_CONFIG['LOCKOUT_DURATION']:
                            is_locked = True
                            lockout_remaining = SECURITY_CONFIG['LOCKOUT_DURATION'] - time_diff
                
                return {
                    'is_locked': is_locked,
                    'lockout_remaining': lockout_remaining,
                    'ip_attempts': ip_attempts,
                    'email_attempts': email_attempts,
                    'max_attempts': SECURITY_CONFIG['MAX_LOGIN_ATTEMPTS']
                }
                
        except Exception as e:
            self.security_logger.error(f"Erro ao verificar tentativas de login: {e}")
            return {'is_locked': False, 'lockout_remaining': 0, 'ip_attempts': 0, 'email_attempts': 0}
    
    def record_login_attempt(self, ip_address: str, email: str, success: bool):
        """Registrar tentativa de login"""
        try:
            user_agent = request.headers.get('User-Agent', '')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO login_attempts (ip_address, email, success, user_agent)
                    VALUES (?, ?, ?, ?)
                ''', (ip_address, email, success, user_agent))
                conn.commit()
            
            # Se muitas tentativas falhadas, considerar blacklist
            if not success:
                attempts_info = self.check_login_attempts(ip_address, email)
                if attempts_info['ip_attempts'] >= SECURITY_CONFIG['MAX_LOGIN_ATTEMPTS'] * 2:
                    self.add_ip_to_blacklist(
                        ip_address, 
                        f"Múltiplas tentativas de login falhadas: {attempts_info['ip_attempts']}", 
                        60  # 1 hora
                    )
                
        except Exception as e:
            self.security_logger.error(f"Erro ao registrar tentativa de login: {e}")
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validar força da senha"""
        issues = []
        score = 0
        
        if len(password) < SECURITY_CONFIG['PASSWORD_MIN_LENGTH']:
            issues.append(f"Senha deve ter pelo menos {SECURITY_CONFIG['PASSWORD_MIN_LENGTH']} caracteres")
        else:
            score += 1
        
        if SECURITY_CONFIG['PASSWORD_REQUIRE_UPPERCASE'] and not re.search(r'[A-Z]', password):
            issues.append("Senha deve conter pelo menos uma letra maiúscula")
        else:
            score += 1
        
        if SECURITY_CONFIG['PASSWORD_REQUIRE_NUMBERS'] and not re.search(r'\d', password):
            issues.append("Senha deve conter pelo menos um número")
        else:
            score += 1
        
        if SECURITY_CONFIG['PASSWORD_REQUIRE_SPECIAL'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Senha deve conter pelo menos um caractere especial")
        else:
            score += 1
        
        # Verificar padrões comuns
        common_patterns = ['123456', 'password', 'admin', 'qwerty', 'abc123']
        if any(pattern in password.lower() for pattern in common_patterns):
            issues.append("Senha não pode conter padrões comuns")
            score -= 1
        
        strength = 'WEAK'
        if score >= 4:
            strength = 'STRONG'
        elif score >= 2:
            strength = 'MEDIUM'
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'strength': strength,
            'score': score
        }
    
    def sanitize_input(self, data: Any) -> Any:
        """Sanitizar entrada de dados"""
        if isinstance(data, str):
            # Remover caracteres perigosos
            data = re.sub(r'[<>"\']', '', data)
            # Limitar tamanho
            if len(data) > 1000:
                data = data[:1000]
            return data.strip()
        elif isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        return data
    
    def generate_csrf_token(self) -> str:
        """Gerar token CSRF"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return session['csrf_token']
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validar token CSRF"""
        return token and token == session.get('csrf_token')
    
    def create_secure_session(self, user_id: int) -> str:
        """Criar sessão segura"""
        try:
            session_token = secrets.token_urlsafe(64)
            ip_address = self.get_client_ip()
            user_agent = request.headers.get('User-Agent', '')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Invalidar sessões antigas do usuário (limite de 3 sessões ativas)
                cursor.execute('''
                    UPDATE active_sessions SET is_active = 0 
                    WHERE user_id = ? AND id NOT IN (
                        SELECT id FROM active_sessions 
                        WHERE user_id = ? AND is_active = 1 
                        ORDER BY last_activity DESC LIMIT 2
                    )
                ''', (user_id, user_id))
                
                # Criar nova sessão
                cursor.execute('''
                    INSERT INTO active_sessions (user_id, session_token, ip_address, user_agent)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, session_token, ip_address, user_agent))
                
                conn.commit()
            
            # Configurar sessão Flask
            session['user_id'] = user_id
            session['session_token'] = session_token
            session['login_time'] = time.time()
            session.permanent = True
            
            self.log_security_event('SESSION_CREATED', {
                'user_id': user_id,
                'session_token': session_token[:16] + '...',  # Log parcial por segurança
                'ip_address': ip_address
            })
            
            return session_token
            
        except Exception as e:
            self.security_logger.error(f"Erro ao criar sessão segura: {e}")
            return None
    
    def validate_session(self, user_id: int, session_token: str) -> bool:
        """Validar sessão ativa"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, last_activity FROM active_sessions 
                    WHERE user_id = ? AND session_token = ? AND is_active = 1
                ''', (user_id, session_token))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                session_id, last_activity = result
                last_time = datetime.fromisoformat(last_activity)
                
                # Verificar timeout
                if (datetime.now() - last_time).total_seconds() > SECURITY_CONFIG['SESSION_TIMEOUT']:
                    # Invalidar sessão expirada
                    cursor.execute('''
                        UPDATE active_sessions SET is_active = 0 WHERE id = ?
                    ''', (session_id,))
                    conn.commit()
                    return False
                
                # Atualizar última atividade
                cursor.execute('''
                    UPDATE active_sessions SET last_activity = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (session_id,))
                conn.commit()
                
                return True
                
        except Exception as e:
            self.security_logger.error(f"Erro ao validar sessão: {e}")
            return False
    
    def cleanup_expired_data(self):
        """Limpar dados expirados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Limpar tentativas de login antigas
                cursor.execute('''
                    DELETE FROM login_attempts 
                    WHERE attempt_time < datetime('now', '-7 days')
                ''')
                
                # Limpar logs de auditoria antigos
                retention_days = SECURITY_CONFIG['AUDIT_LOG_RETENTION_DAYS']
                cursor.execute('''
                    DELETE FROM audit_log 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(retention_days))
                
                # Limpar sessões inativas
                cursor.execute('''
                    DELETE FROM active_sessions 
                    WHERE is_active = 0 OR last_activity < datetime('now', '-1 day')
                ''')
                
                # Limpar blacklist expirada
                cursor.execute('''
                    UPDATE ip_blacklist SET is_active = 0 
                    WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
                ''')
                
                conn.commit()
                
                self.security_logger.info("Limpeza de dados de segurança concluída")
                
        except Exception as e:
            self.security_logger.error(f"Erro na limpeza de dados: {e}")

# Decoradores de segurança
def require_auth(f):
    """Decorador para exigir autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'session_token' not in session:
            return jsonify({'error': 'Autenticação necessária'}), 401
        
        # Validar sessão
        security_manager = getattr(g, 'security_manager', None)
        if security_manager:
            user_id = session['user_id']
            session_token = session['session_token']
            
            if not security_manager.validate_session(user_id, session_token):
                session.clear()
                return jsonify({'error': 'Sessão expirada'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_permission(permission):
    """Decorador para exigir permissão específica"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Primeiro verificar autenticação
            if 'user_id' not in session:
                return jsonify({'error': 'Autenticação necessária'}), 401
            
            # Verificar permissão (implementar conforme seu sistema)
            # Por enquanto, apenas log da verificação
            security_manager = getattr(g, 'security_manager', None)
            if security_manager:
                security_manager.log_security_event('PERMISSION_CHECK', {
                    'permission': permission,
                    'user_id': session['user_id']
                })
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_csrf(f):
    """Decorador para exigir token CSRF"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            
            security_manager = getattr(g, 'security_manager', None)
            if security_manager and not security_manager.validate_csrf_token(token):
                security_manager.log_security_event('CSRF_VIOLATION', {
                    'endpoint': request.endpoint,
                    'method': request.method
                }, 'HIGH')
                return jsonify({'error': 'Token CSRF inválido'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def check_ip_blacklist(f):
    """Decorador para verificar blacklist de IP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        security_manager = getattr(g, 'security_manager', None)
        if security_manager:
            ip_address = security_manager.get_client_ip()
            
            if security_manager.is_ip_blacklisted(ip_address):
                security_manager.log_security_event('BLACKLISTED_ACCESS_ATTEMPT', {
                    'ip_address': ip_address,
                    'endpoint': request.endpoint
                }, 'HIGH')
                return jsonify({'error': 'Acesso negado'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Classe para validação de entrada
class InputValidator:
    """Validador de entrada de dados"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validar formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) <= 255
    
    @staticmethod
    def validate_rnc_number(rnc_number: str) -> bool:
        """Validar número de RNC"""
        pattern = r'^RNC-\d{4}-\d{4,6}$'
        return bool(re.match(pattern, rnc_number))
    
    @staticmethod
    def validate_text_field(text: str, max_length: int = 1000) -> bool:
        """Validar campo de texto"""
        if not isinstance(text, str):
            return False
        
        # Verificar tamanho
        if len(text) > max_length:
            return False
        
        # Verificar caracteres perigosos
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def validate_numeric_field(value: str, min_val: float = None, max_val: float = None) -> bool:
        """Validar campo numérico"""
        try:
            num_val = float(value)
            
            if min_val is not None and num_val < min_val:
                return False
            
            if max_val is not None and num_val > max_val:
                return False
            
            return True
        except ValueError:
            return False

# Configuração de headers de segurança
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
    'Content-Security-Policy': (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "style-src-elem 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' data: https://fonts.gstatic.com https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )
}

def add_security_headers(response):
    """Adicionar headers de segurança"""
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response
