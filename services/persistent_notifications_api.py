#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🔔 Sistema de Notificações Persistentes - Frontend
Sistema que mostra notificações "chatas" até o usuário responder
"""

import sqlite3
import os
from flask import Blueprint, jsonify, request, session
import logging

logger = logging.getLogger(__name__)

# Blueprint para as APIs de notificações persistentes
persistent_notifications_bp = Blueprint('persistent_notifications', __name__)

DB_PATH = 'ippel_system.db'


def get_db_connection(timeout=30):
    """Retorna conexão SQLite com timeout para evitar database locked"""
    conn = sqlite3.connect(DB_PATH, timeout=timeout)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def init_persistent_notifications_tables():
    """Criar tabelas necessárias para notificações persistentes"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tabela de notificações de alterações em RNC
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rnc_change_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rnc_id INTEGER NOT NULL,
                change_type TEXT NOT NULL,
                change_details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by_user_id INTEGER,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (rnc_id) REFERENCES rncs(id),
                FOREIGN KEY (created_by_user_id) REFERENCES users(id)
            )
        """)
        
        # Tabela de destinatários das notificações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rnc_notification_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                is_responded INTEGER DEFAULT 0,
                response_text TEXT,
                responded_at TIMESTAMP,
                is_dismissed INTEGER DEFAULT 0,
                dismissed_at TIMESTAMP,
                FOREIGN KEY (notification_id) REFERENCES rnc_change_notifications(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Tabela de histórico de respostas de causa da RNC
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rnc_cause_response_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rnc_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                cause_text TEXT,
                action_type TEXT DEFAULT 'create',  -- create, update
                previous_cause TEXT,
                responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notification_id INTEGER,
                FOREIGN KEY (rnc_id) REFERENCES rncs(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("✅ Tabelas de notificações persistentes criadas/verificadas")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas de notificações persistentes: {e}")
        return False


def create_pending_notification(rnc_id, change_type, target_user_ids, created_by_user_id, change_details=None):
    """
    Criar uma notificação persistente para usuários específicos
    
    Args:
        rnc_id: ID da RNC
        change_type: Tipo de mudança (create, update, reply, share, etc.)
        target_user_ids: Lista de IDs de usuários que devem ver a pendência
        created_by_user_id: ID do usuário que criou a notificação
        change_details: Detalhes adicionais (JSON string)
    """
    try:
        import json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Criar notificação principal
        cursor.execute("""
            INSERT INTO rnc_change_notifications (rnc_id, change_type, change_details, created_by_user_id)
            VALUES (?, ?, ?, ?)
        """, (rnc_id, change_type, json.dumps(change_details) if change_details else None, created_by_user_id))
        
        notification_id = cursor.lastrowid
        
        # Criar registros para cada destinatário
        for user_id in target_user_ids:
            if user_id != created_by_user_id:  # Não notificar quem criou
                cursor.execute("""
                    INSERT INTO rnc_notification_recipients (notification_id, user_id)
                    VALUES (?, ?)
                """, (notification_id, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Pendência criada: RNC {rnc_id}, tipo {change_type}, para {len(target_user_ids)} usuários")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar pendência: {e}")
        return False


@persistent_notifications_bp.route('/api/persistent-notifications/pending', methods=['GET'])
def get_pending_notifications():
    """API para buscar notificações pendentes (não respondidas) do usuário"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    user_id = session['user_id']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar notificações persistentes não respondidas e não dispensadas
        cursor.execute("""
            SELECT 
                pn.id,
                pn.rnc_id,
                pn.change_type,
                pn.change_details,
                pn.created_at,
                pn.created_by_user_id,
                u.name as created_by_name,
                u.department as created_by_dept,
                r.title as rnc_title,
                r.rnc_number as rnc_number
            FROM rnc_change_notifications pn
            LEFT JOIN users u ON pn.created_by_user_id = u.id
            LEFT JOIN rncs r ON pn.rnc_id = r.id
            WHERE pn.id IN (
                SELECT notification_id 
                FROM rnc_notification_recipients 
                WHERE user_id = ? AND is_responded = 0 AND is_dismissed = 0
            )
            ORDER BY pn.created_at DESC
            LIMIT 10
        """, (user_id,))
        
        notifications = []
        for row in cursor.fetchall():
            notification_id, rnc_id, change_type, change_details, created_at, created_by_user_id, created_by_name, created_by_dept, rnc_title, rnc_number = row
            
            # Parse change_details se for JSON
            try:
                import json
                details = json.loads(change_details) if change_details else {}
            except:
                details = {}
            
            # Criar mensagem baseada no tipo
            if change_type == 'create':
                message = f"📝 {created_by_name} criou uma nova RNC: {rnc_title}"
                action_text = "Ver RNC"
            elif change_type == 'update':
                message = f"✏️ {created_by_name} atualizou a RNC: {rnc_title}"
                action_text = "Ver Alterações"
            elif change_type == 'chat_response':
                chat_msg = details.get('message', '')[:50] + ('...' if len(details.get('message', '')) > 50 else '')
                message = f"💬 {created_by_name} respondeu: {chat_msg}"
                action_text = "Ver Chat"
            else:
                message = f"🔔 {created_by_name} fez alterações na RNC: {rnc_title}"
                action_text = "Ver RNC"
            
            notifications.append({
                'id': notification_id,
                'rnc_id': rnc_id,
                'rnc_number': rnc_number,
                'rnc_title': rnc_title,
                'change_type': change_type,
                'message': message,
                'action_text': action_text,
                'created_at': created_at,
                'created_by_name': created_by_name,
                'created_by_dept': created_by_dept,
                'details': details
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar notificações pendentes: {e}")
        return jsonify({'success': False, 'message': 'Erro interno'}), 500

@persistent_notifications_bp.route('/api/persistent-notifications/<int:notification_id>/respond', methods=['POST'])
def respond_to_notification(notification_id):
    """API para marcar notificação como respondida"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    user_id = session['user_id']
    data = request.get_json() or {}
    response_text = data.get('response', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Marcar como respondida
        cursor.execute("""
            UPDATE rnc_notification_recipients
            SET is_responded = 1, 
                response_text = ?,
                responded_at = CURRENT_TIMESTAMP
            WHERE notification_id = ? AND user_id = ?
        """, (response_text, notification_id, user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Notificação não encontrada'}), 404
        
        conn.commit()
        conn.close()
        
        # Limpar cache para atualizar lista de RNCs
        try:
            from services.cache import clear_rnc_cache
            clear_rnc_cache()
        except Exception:
            pass
        
        logger.info(f"✅ Usuário {user_id} respondeu à notificação {notification_id}")
        
        return jsonify({
            'success': True,
            'message': 'Resposta registrada com sucesso!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao responder notificação {notification_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro interno'}), 500

@persistent_notifications_bp.route('/api/persistent-notifications/<int:notification_id>/dismiss', methods=['POST'])
def dismiss_notification(notification_id):
    """API para dispensar notificação temporariamente (não remove, mas para de incomodar)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    user_id = session['user_id']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Marcar como temporariamente dispensada (mas não respondida)
        cursor.execute("""
            UPDATE rnc_notification_recipients
            SET is_dismissed = 1,
                dismissed_at = CURRENT_TIMESTAMP
            WHERE notification_id = ? AND user_id = ?
        """, (notification_id, user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Notificação não encontrada'}), 404
        
        conn.commit()
        conn.close()
        
        logger.info(f"📵 Usuário {user_id} dispensou temporariamente a notificação {notification_id}")
        
        return jsonify({
            'success': True,
            'message': 'Notificação dispensada'
        })
        
    except Exception as e:
        logger.error(f"Erro ao dispensar notificação {notification_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro interno'}), 500


# ============================================================
# ROTAS DE ADMIN - Gerenciar notificações
# ============================================================

@persistent_notifications_bp.route('/api/admin/notifications/responded', methods=['GET'])
def get_responded_notifications():
    """API para admin ver notificações já respondidas"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    # Verificar se é admin
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        if not user or user[0] != 'admin':
            conn.close()
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Buscar notificações respondidas (últimas 50)
        cursor.execute("""
            SELECT 
                rnr.id,
                rnr.notification_id,
                rnr.user_id,
                u.name as user_name,
                rnr.response_text,
                rnr.responded_at,
                rcn.rnc_id,
                r.rnc_number,
                r.title as rnc_title,
                rcn.change_type,
                rcn.change_details
            FROM rnc_notification_recipients rnr
            INNER JOIN rnc_change_notifications rcn ON rnr.notification_id = rcn.id
            LEFT JOIN users u ON rnr.user_id = u.id
            LEFT JOIN rncs r ON rcn.rnc_id = r.id
            WHERE rnr.is_responded = 1
            ORDER BY rnr.responded_at DESC
            LIMIT 50
        """)
        
        notifications = []
        for row in cursor.fetchall():
            (recipient_id, notification_id, user_id, user_name, response_text, 
             responded_at, rnc_id, rnc_number, rnc_title, change_type, change_details) = row
            
            notifications.append({
                'recipient_id': recipient_id,
                'notification_id': notification_id,
                'user_id': user_id,
                'user_name': user_name or 'Usuário',
                'response_text': response_text or '',
                'responded_at': responded_at,
                'rnc_id': rnc_id,
                'rnc_number': rnc_number,
                'rnc_title': rnc_title or 'RNC',
                'change_type': change_type
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar notificações respondidas: {e}")
        return jsonify({'success': False, 'message': 'Erro interno'}), 500


@persistent_notifications_bp.route('/api/admin/notifications/<int:notification_id>/reopen', methods=['POST'])
def reopen_notification(notification_id):
    """API para admin reabrir notificação (voltar para usuário ver)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    data = request.get_json() or {}
    target_user_id = data.get('user_id')
    
    if not target_user_id:
        return jsonify({'success': False, 'message': 'user_id é obrigatório'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se é admin
        cursor.execute("SELECT role FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        if not user or user[0] != 'admin':
            conn.close()
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Reabrir notificação (marcar como não respondida)
        cursor.execute("""
            UPDATE rnc_notification_recipients
            SET is_responded = 0,
                response_text = NULL,
                responded_at = NULL,
                is_dismissed = 0,
                dismissed_at = NULL
            WHERE notification_id = ? AND user_id = ?
        """, (notification_id, target_user_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Notificação não encontrada'}), 404
        
        conn.commit()
        conn.close()
        
        # Limpar cache de RNCs para que o usuário veja a RNC novamente
        try:
            from services.cache import clear_rnc_cache
            clear_rnc_cache()
            logger.info(f"🗑️ Cache de RNCs limpo após reabrir pendência")
        except Exception as e:
            logger.warning(f"Erro ao limpar cache: {e}")
        
        logger.info(f"🔄 Admin {session['user_id']} reabriu notificação {notification_id} para usuário {target_user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Notificação reaberta com sucesso! O usuário verá a pendência novamente.'
        })
        
    except Exception as e:
        logger.error(f"Erro ao reabrir notificação {notification_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro interno'}), 500


def register_persistent_notifications_routes(app):
    """Registrar as rotas de notificações persistentes no app Flask"""
    # Criar tabelas se não existirem
    init_persistent_notifications_tables()
    
    app.register_blueprint(persistent_notifications_bp)
    logger.info("✅ Rotas de notificações persistentes registradas")
