import logging
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, render_template, redirect, session

DB_PATH = 'ippel_system.db'
DATABASE_PATH = 'ippel_system.db'

# Timezone de Brasília (UTC-3)
BRASILIA_TZ = timezone(timedelta(hours=-3))

def get_brasilia_now():
    """Retorna datetime atual no horário de Brasília"""
    return datetime.now(BRASILIA_TZ)

def get_brasilia_timestamp():
    """Retorna timestamp formatado no horário de Brasília"""
    return get_brasilia_now().strftime('%Y-%m-%d %H:%M:%S')

ro = Blueprint('ro', __name__)
logger = logging.getLogger('ippel.ro')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


@ro.route('/api/ro/list', methods=['GET'])
def list_ros():
    """Lista todos os R.O ativos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                r.*,
                u.name as creator_name,
                u.department as creator_department,
                au.name as assigned_user_name
            FROM ros r
            LEFT JOIN users u ON r.user_id = u.id
            LEFT JOIN users au ON r.assigned_user_id = au.id
            WHERE r.is_deleted = 0 AND r.finalized_at IS NULL
            ORDER BY r.created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        ros = []
        for row in rows:
            ro_dict = dict(row)
            ros.append(ro_dict)
        
        return jsonify({'success': True, 'ros': ros})
    except Exception as e:
        logger.error(f"Erro ao listar R.O: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ro.route('/api/ro/finalized', methods=['GET'])
def list_finalized_ros():
    """Lista R.O finalizados"""
    try:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 50))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                r.*,
                u.name as creator_name,
                u.department as creator_department
            FROM ros r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.is_deleted = 0 AND r.finalized_at IS NOT NULL
            ORDER BY r.finalized_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        
        # Contar total
        cursor.execute('''
            SELECT COUNT(*) as total 
            FROM ros 
            WHERE is_deleted = 0 AND finalized_at IS NOT NULL
        ''')
        total = cursor.fetchone()['total']
        
        conn.close()
        
        ros = [dict(row) for row in rows]
        
        return jsonify({
            'success': True,
            'ros': ros,
            'total': total,
            'hasMore': (offset + limit) < total
        })
    except Exception as e:
        logger.error(f"Erro ao listar R.O finalizados: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ro.route('/api/ro/create', methods=['POST'])
def create_ro():
    """Cria um novo R.O"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Gerar número do R.O (apenas considerando R.Os ativas)
        cursor.execute('SELECT MAX(CAST(ro_number AS INTEGER)) as max_num FROM ros WHERE is_deleted = 0')
        result = cursor.fetchone()
        next_number = (result['max_num'] or 0) + 1
        
        # Data/hora atual no horário de Brasília
        brasilia_now = get_brasilia_timestamp()
        
        # Inserir R.O com todos os campos
        cursor.execute('''
            INSERT INTO ros (
                ro_number, title, description, equipment, client,
                priority, status, user_id, created_at,
                drawing_number, revision, conjunto, description_drawing,
                position, modelo, material, quantity, cv, mp,
                area_responsavel, ass_responsavel, inspetor, responsavel,
                setor, purchase_order, instruction_retrabalho, cause_ro,
                price, price_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(next_number),
            data.get('title'),
            data.get('description'),
            data.get('equipment'),
            data.get('client'),
            data.get('priority', 'Média'),
            'Pendente',
            user_id,
            brasilia_now,  # Usa horário de Brasília
            data.get('drawing_number'),
            data.get('revision'),
            data.get('conjunto'),
            data.get('description_drawing'),
            data.get('position'),
            data.get('modelo'),
            data.get('material'),
            data.get('quantity'),
            data.get('cv'),
            data.get('mp'),
            data.get('area_responsavel'),
            data.get('ass_responsavel'),
            data.get('inspetor'),
            data.get('responsavel'),
            data.get('setor'),
            data.get('purchase_order'),
            data.get('instruction_retrabalho'),
            data.get('cause_ro'),
            data.get('price'),
            data.get('price_note')
        ))
        
        ro_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log de auditoria
        try:
            from services.audit import log_event
            log_event('RO_CREATE', f'R.O #{next_number} criado',
                      target_type='RO', target_id=ro_id,
                      user_id=user_id, user_name=session.get('user_name'),
                      ip_address=request.remote_addr)
        except Exception:
            pass
        
        return jsonify({
            'success': True,
            'ro_id': ro_id,
            'ro_number': str(next_number)
        })
    except Exception as e:
        logger.error(f"Erro ao criar R.O: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ro.route('/api/ro/<int:ro_id>', methods=['GET'])
def get_ro(ro_id):
    """Retorna dados de um R.O específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                r.*,
                u.name as creator_name,
                u.department as creator_department
            FROM ros r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
        ''', (ro_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': 'R.O não encontrado'}), 404
        
        return jsonify({'success': True, 'ro': dict(row)})
    except Exception as e:
        logger.error(f"Erro ao buscar R.O: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ro.route('/api/ro/<int:ro_id>/update', methods=['PUT']) 
def update_ro(ro_id):
    """Atualiza um R.O"""
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Campos permitidos para atualização
        allowed_fields = [
            'title', 'description', 'equipment', 'client', 'priority',
            'status', 'price', 'disposition_usar', 'disposition_retrabalhar',
            'disposition_rejeitar', 'disposition_sucata', 
            'disposition_devolver_estoque', 'disposition_devolver_fornecedor',
            'inspection_aprovado', 'inspection_reprovado', 'inspection_ver_ro',
            'signature_inspection_date', 'signature_engineering_date',
            'signature_inspection2_date', 'signature_inspection_name',
            'signature_engineering_name', 'signature_inspection2_name',
            'ass_responsavel'
        ]
        
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = ?")
                values.append(data[field])
        
        if updates:
            brasilia_now = get_brasilia_timestamp()
            values.append(brasilia_now)
            values.append(ro_id)
            sql = f"UPDATE ros SET {', '.join(updates)}, updated_at = ? WHERE id = ?"
            cursor.execute(sql, values)
            conn.commit()
        
        conn.close()
        
        # Log de auditoria
        try:
            from services.audit import log_event
            log_event('RO_UPDATE', f'R.O #{ro_id} atualizado',
                      target_type='RO', target_id=ro_id,
                      user_id=session.get('user_id'), user_name=session.get('user_name'),
                      ip_address=request.remote_addr)
        except Exception:
            pass
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erro ao atualizar R.O: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ro.route('/api/ro/<int:ro_id>/finalize', methods=['POST'])
def finalize_ro(ro_id):
    """Finaliza um R.O"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        brasilia_now = get_brasilia_timestamp()
        cursor.execute('''
            UPDATE ros 
            SET status = 'Finalizado', 
                finalized_at = ? 
            WHERE id = ?
        ''', (brasilia_now, ro_id))
        
        conn.commit()
        conn.close()
        
        # Log de auditoria
        try:
            from services.audit import log_event
            log_event('RO_FINALIZE', f'R.O #{ro_id} finalizado',
                      target_type='RO', target_id=ro_id,
                      user_id=session.get('user_id'), user_name=session.get('user_name'),
                      ip_address=request.remote_addr)
        except Exception:
            pass
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erro ao finalizar R.O: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ro.route('/api/ro/<int:ro_id>/delete', methods=['DELETE'])
def delete_ro(ro_id):
    """Marca R.O como deletado"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        brasilia_now = get_brasilia_timestamp()
        
        cursor.execute('''
            UPDATE ros 
            SET is_deleted = 1, deleted_at = ? 
            WHERE id = ?
        ''', (brasilia_now, ro_id))
        
        conn.commit()
        conn.close()
        
        # Log de auditoria
        try:
            from services.audit import log_event
            log_event('RO_DELETE', f'R.O #{ro_id} excluído',
                      target_type='RO', target_id=ro_id,
                      user_id=session.get('user_id'), user_name=session.get('user_name'),
                      ip_address=request.remote_addr)
        except Exception:
            pass
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erro ao deletar R.O: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
