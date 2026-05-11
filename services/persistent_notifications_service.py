#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🔔 Serviço de Notificações Persistentes
Sistema que cria notificações "chatas" que só param quando o usuário responder
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class PersistentNotificationService:
    def __init__(self, db_path: str = 'ippel_system.db'):
        self.db_path = db_path
    
    def log_rnc_change(self, rnc_id: int, change_type: str, change_details: Dict, 
                       created_by_user_id: int) -> Optional[int]:
        """
        Registra uma mudança na RNC e cria notificações persistentes
        
        Args:
            rnc_id: ID da RNC
            change_type: Tipo de mudança ('create', 'update', 'chat_response', 'value_addition')
            change_details: Detalhes da mudança em formato dict
            created_by_user_id: ID do usuário que fez a mudança
            
        Returns:
            ID da notificação criada ou None se houver erro
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Inserir notificação principal
            cursor.execute("""
                INSERT INTO rnc_change_notifications (rnc_id, change_type, change_details, created_by_user_id)
                VALUES (?, ?, ?, ?)
            """, (rnc_id, change_type, json.dumps(change_details, ensure_ascii=False), created_by_user_id))
            
            notification_id = cursor.lastrowid
            
            # Buscar usuários que devem ser notificados (baseado em compartilhamentos e grupos)
            target_users = self.get_target_users(rnc_id, created_by_user_id, cursor)
            
            # Criar registros de destinatários para cada usuário
            for user_id in target_users:
                cursor.execute("""
                    INSERT INTO rnc_notification_recipients (notification_id, user_id)
                    VALUES (?, ?)
                """, (notification_id, user_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Mudança RNC {rnc_id} registrada. {len(target_users)} usuários notificados.")
            return notification_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar mudança RNC {rnc_id}: {e}")
            return None
    
    def get_target_users(self, rnc_id: int, created_by_user_id: int, cursor) -> List[int]:
        """
        Busca os usuários que devem receber notificações sobre mudanças nesta RNC
        
        Args:
            rnc_id: ID da RNC
            created_by_user_id: ID do usuário que fez a mudança (será excluído das notificações)
            cursor: Cursor da base de dados
            
        Returns:
            Lista de IDs de usuários que devem ser notificados
        """
        try:
            target_users = set()
            
            # 1. Buscar o responsável pela RNC
            cursor.execute("SELECT assigned_user_id FROM rncs WHERE id = ?", (rnc_id,))
            result = cursor.fetchone()
            if result and result[0] and result[0] != created_by_user_id:
                target_users.add(result[0])
            
            # 2. Buscar SOMENTE usuários com quem a RNC foi compartilhada explicitamente
            # (causador, gerente, subgerente - definidos em main_system.py)
            cursor.execute("""
                SELECT shared_with_user_id 
                FROM rnc_shares 
                WHERE rnc_id = ? AND shared_with_user_id != ?
            """, (rnc_id, created_by_user_id))
            
            for row in cursor.fetchall():
                if row[0]:
                    target_users.add(row[0])
            
            # REMOVIDO: Não notificar todos os membros do grupo
            # Apenas usuários explicitamente compartilhados recebem notificação
            
            return list(target_users)
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar usuários alvo para RNC {rnc_id}: {e}")
            return []
    
    def get_pending_notifications(self, user_id: int) -> List[Dict]:
        """
        Busca notificações pendentes (não respondidas) para um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de notificações pendentes
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    rcn.id,
                    rcn.rnc_id,
                    rcn.change_type,
                    rcn.change_details,
                    rcn.created_at,
                    rcn.created_by_user_id,
                    u.name as created_by_name,
                    r.title as rnc_title,
                    r.rnc_number
                FROM rnc_change_notifications rcn
                INNER JOIN rnc_notification_recipients rnr ON rcn.id = rnr.notification_id
                LEFT JOIN users u ON rcn.created_by_user_id = u.id
                LEFT JOIN rncs r ON rcn.rnc_id = r.id
                WHERE rnr.user_id = ? 
                AND rnr.is_responded = 0 
                AND rnr.is_dismissed = 0
                AND rcn.is_active = 1
                ORDER BY rcn.created_at DESC
                LIMIT 10
            """, (user_id,))
            
            notifications = []
            for row in cursor.fetchall():
                notification_id, rnc_id, change_type, change_details, created_at, created_by_user_id, created_by_name, rnc_title, rnc_number = row
                
                # Parse change_details
                try:
                    details = json.loads(change_details) if change_details else {}
                except:
                    details = {}
                
                notifications.append({
                    'id': notification_id,
                    'rnc_id': rnc_id,
                    'rnc_number': rnc_number,
                    'rnc_title': rnc_title,
                    'change_type': change_type,
                    'details': details,
                    'created_at': created_at,
                    'created_by_user_id': created_by_user_id,
                    'created_by_name': created_by_name
                })
            
            conn.close()
            return notifications
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar notificações pendentes para usuário {user_id}: {e}")
            return []
    
    def mark_as_responded(self, notification_id: int, user_id: int, response_text: str = '') -> bool:
        """
        Marca uma notificação como respondida por um usuário
        
        Args:
            notification_id: ID da notificação
            user_id: ID do usuário que respondeu
            response_text: Texto da resposta (opcional)
            
        Returns:
            True se marcado com sucesso, False caso contrário
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE rnc_notification_recipients
                SET is_responded = 1,
                    response_text = ?,
                    responded_at = CURRENT_TIMESTAMP
                WHERE notification_id = ? AND user_id = ?
            """, (response_text, notification_id, user_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"✅ Notificação {notification_id} marcada como respondida pelo usuário {user_id}")
            else:
                logger.warning(f"⚠️ Notificação {notification_id} não encontrada para usuário {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao marcar notificação {notification_id} como respondida: {e}")
            return False
    
    def dismiss_temporarily(self, notification_id: int, user_id: int) -> bool:
        """
        Marca uma notificação como temporariamente dispensada (não remove, mas para de incomodar)
        
        Args:
            notification_id: ID da notificação
            user_id: ID do usuário
            
        Returns:
            True se dispensada com sucesso, False caso contrário
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE rnc_notification_recipients
                SET is_dismissed = 1,
                    dismissed_at = CURRENT_TIMESTAMP
                WHERE notification_id = ? AND user_id = ?
            """, (notification_id, user_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"📵 Notificação {notification_id} dispensada temporariamente pelo usuário {user_id}")
            else:
                logger.warning(f"⚠️ Notificação {notification_id} não encontrada para usuário {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao dispensar notificação {notification_id}: {e}")
            return False
    
    def get_notification_count(self, user_id: int) -> int:
        """
        Conta o número de notificações pendentes para um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Número de notificações pendentes
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*)
                FROM rnc_change_notifications rcn
                INNER JOIN rnc_notification_recipients rnr ON rcn.id = rnr.notification_id
                WHERE rnr.user_id = ? 
                AND rnr.is_responded = 0 
                AND rnr.is_dismissed = 0
                AND rcn.is_active = 1
            """, (user_id,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Erro ao contar notificações para usuário {user_id}: {e}")
            return 0
    
    def deactivate_old_notifications(self, days_old: int = 30) -> int:
        """
        Desativa notificações antigas para não sobrecarregar o sistema
        
        Args:
            days_old: Idade em dias para considerar notificações como antigas
            
        Returns:
            Número de notificações desativadas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE rnc_change_notifications
                SET is_active = 0
                WHERE is_active = 1 
                AND datetime(created_at) < datetime('now', '-{} days')
            """.format(days_old))
            
            deactivated_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deactivated_count > 0:
                logger.info(f"🧹 {deactivated_count} notificações antigas desativadas")
            
            return deactivated_count
            
        except Exception as e:
            logger.error(f"❌ Erro ao desativar notificações antigas: {e}")
            return 0