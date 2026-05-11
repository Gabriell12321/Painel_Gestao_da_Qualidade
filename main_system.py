#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTEMA PRINCIPAL - RELATÓRIOS DE NÃO CONFORMIDADES IPPEL
Sistema completo com banco de dados, email bidirecional e interface web
"""

import sqlite3
import os
import logging
import threading
import time
import datetime
import uuid
import secrets
import random

# Import do sistema de notificações persistentes
try:
    from services.persistent_notifications_service import PersistentNotificationService
    from services.persistent_notifications_api import register_persistent_notifications_routes
    notification_service = PersistentNotificationService()
except ImportError as e:
    logging.warning(f"Sistema de notificações persistentes não disponível: {e}")
    notification_service = None
import hashlib
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from services.security_enhancements import add_security_headers

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'ippel_secret_key_default_change_me')

# Configurar Flask-SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configurações do banco
DB_PATH = 'ippel_system.db'

# Backup: diretório de destino no Windows (fornecido pelo cliente)
BACKUP_DIR = r'G:\Meu Drive\BACKUP BANCO DE DADOS IPPEL'

import threading
import time
import datetime

def ensure_backup_dir_exists() -> None:
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
    except Exception as e:
        print(f"Erro ao criar diretório de backup '{BACKUP_DIR}': {e}")

def backup_database_now() -> None:
    """Snapshot consistente utilizando API de backup do SQLite."""
    ensure_backup_dir_exists()
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(BACKUP_DIR, f"ippel_system_{ts}.db")
    try:
        src = sqlite3.connect(DB_PATH, timeout=30.0)
        dst = sqlite3.connect(dest, timeout=30.0)
        with dst:
            src.backup(dst)
        src.close(); dst.close()
        print(f"✅ Backup criado: {dest}")
    except Exception as e:
        print(f"⚠️ Erro ao criar backup: {e}")

def start_backup_scheduler(interval_seconds: int = 480) -> None:
    def _run():
        # Backup imediato ao iniciar
        backup_database_now()
        while True:
            time.sleep(interval_seconds)
            backup_database_now()
    threading.Thread(target=_run, name='BackupScheduler', daemon=True).start()

class User(UserMixin):
    def __init__(self, id, name, email, department, role):
        self.id = id
        self.name = name
        self.email = email
        self.department = department
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, email, department, role 
            FROM users WHERE id = ?
        """, (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4])
        return None
    except Exception as e:
        logger.error(f"Erro ao carregar usuário: {e}")
        return None

def init_database():
    """Inicializar banco de dados se não existir"""
    if not os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Criar tabelas
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    department TEXT,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE rnc_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rnc_number TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    equipment TEXT,
                    client TEXT,
                    priority TEXT DEFAULT 'Média',
                    status TEXT DEFAULT 'Pendente',
                    price REAL DEFAULT 0,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE rnc_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rnc_id INTEGER NOT NULL,
                    item_number INTEGER,
                    description TEXT,
                    instruction TEXT,
                    cause TEXT,
                    action TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (rnc_id) REFERENCES rnc_reports (id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE rnc_signatures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rnc_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    signature_type TEXT NOT NULL,
                    signature_data TEXT,
                    signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (rnc_id) REFERENCES rnc_reports (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Tabela de grupos (para compartilhamento/seleção no formulário)
            cursor.execute('''
                CREATE TABLE groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT DEFAULT ''
                )
            ''')

            # Popular grupos padrão
            default_groups = [
                ('Produção', 'Grupo de Produção'),
                ('Engenharia', 'Grupo de Engenharia'),
                ('Compras', 'Grupo de Compras'),
                ('Comercial', 'Grupo Comercial'),
                ('PCP', 'Planejamento e Controle da Produção'),
                ('Qualidade', 'Grupo de Qualidade'),
                ('Manutenção', 'Grupo de Manutenção'),
                ('Logística', 'Grupo de Logística')
            ]
            cursor.executemany('INSERT OR IGNORE INTO groups (name, description) VALUES (?, ?)', default_groups)
            
            # Inserir usuário admin padrão
            admin_password = generate_password_hash('admin123')
            cursor.execute('''
                INSERT INTO users (name, email, password_hash, department, role)
                VALUES (?, ?, ?, ?, ?)
            ''', ('Administrador', 'admin@ippel.com.br', admin_password, 'Administração', 'admin'))
            
            # Inserir alguns usuários de exemplo
            users_data = [
                ('João Silva', 'joao@ippel.com.br', 'joao123', 'Produção', 'user'),
                ('Maria Santos', 'maria@ippel.com.br', 'maria123', 'Qualidade', 'user'),
                ('Pedro Costa', 'pedro@ippel.com.br', 'pedro123', 'Manutenção', 'user'),
                ('Ana Oliveira', 'ana@ippel.com.br', 'ana123', 'Engenharia', 'user')
            ]
            
            for name, email, password, dept, role in users_data:
                password_hash = generate_password_hash(password)
                cursor.execute('''
                    INSERT INTO users (name, email, password_hash, department, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, email, password_hash, dept, role))
            
            conn.commit()
            conn.close()
            logger.info("Banco de dados inicializado com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco: {e}")

def ensure_schema_migrations():
    """Garantir que a tabela rncs possua a coluna price."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se a tabela rncs existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rncs'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(rncs)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'price' not in columns:
                cursor.execute("ALTER TABLE rncs ADD COLUMN price REAL DEFAULT 0")
                conn.commit()
                logger.info("Migração aplicada: coluna 'price' adicionada em rncs")

        # Garantir tabela de grupos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='groups'")
        if cursor.fetchone() is None:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT DEFAULT ''
                )
            ''')
            default_groups = [
                ('Produção', 'Grupo de Produção'),
                ('Engenharia', 'Grupo de Engenharia'),
                ('Compras', 'Grupo de Compras'),
                ('Comercial', 'Grupo Comercial'),
                ('PCP', 'Planejamento e Controle da Produção'),
                ('Qualidade', 'Grupo de Qualidade'),
                ('Manutenção', 'Grupo de Manutenção'),
                ('Logística', 'Grupo de Logística')
            ]
            cursor.executemany('INSERT OR IGNORE INTO groups (name, description) VALUES (?, ?)', default_groups)
            conn.commit()
            logger.info("Migração aplicada: tabela 'groups' criada e populada")
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao aplicar migração de schema: {e}")

# --- Suporte a clientes (para selects/autocomplete) ---
def ensure_clients_table():
    """Garantir que a tabela 'clients' exista para uso em formulários."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS clients (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT UNIQUE NOT NULL,
                   category TEXT DEFAULT 'Outros',
                   description TEXT,
                   contact_info TEXT,
                   active BOOLEAN DEFAULT 1,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )'''
        )
        
        # Adicionar coluna category se não existir (migração)
        try:
            cursor.execute("PRAGMA table_info(clients)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'category' not in columns:
                cursor.execute("ALTER TABLE clients ADD COLUMN category TEXT DEFAULT 'Outros'")
                logger.info("✅ Coluna 'category' adicionada à tabela clients")
        except Exception as migration_error:
            logger.warning(f"Migração de category ignorada: {migration_error}")
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao garantir tabela clients: {e}")

def migrate_users_table():
    """Migrar tabela users para adicionar campos necessários"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se precisa adicionar group_id
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'group_id' not in columns:
            logger.info("Adicionando campo group_id à tabela users")
            cursor.execute('ALTER TABLE users ADD COLUMN group_id INTEGER')
        
        if 'active' not in columns:
            logger.info("Adicionando campo active à tabela users")
            cursor.execute('ALTER TABLE users ADD COLUMN active BOOLEAN DEFAULT 1')
        
        # Garantir que existe pelo menos um grupo padrão
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='groups'")
        if cursor.fetchone()[0] == 0:
            logger.info("Criando tabela groups")
            cursor.execute('''
                CREATE TABLE groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Inserir grupo padrão se não existir
        cursor.execute("SELECT COUNT(*) FROM groups")
        if cursor.fetchone()[0] == 0:
            logger.info("Criando grupos padrão")
            default_groups = [
                ('Administradores', 'Acesso completo ao sistema'),
                ('Engenharia', 'Equipe de engenharia'),
                ('Qualidade', 'Equipe de controle de qualidade'),
                ('Operadores', 'Operadores de produção'),
                ('Gerentes', 'Gerentes de área com permissões elevadas')
            ]
            
            for name, desc in default_groups:
                cursor.execute("INSERT OR IGNORE INTO groups (name, description) VALUES (?, ?)", (name, desc))
        
        conn.commit()
        conn.close()
        logger.info("Migração da tabela users concluída com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao migrar tabela users: {e}")

class RNCSystem:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Garantir migrações de schema necessárias
        ensure_schema_migrations()
    
    def _get_conn(self):
        """Obter conexão configurada com timeout e WAL."""
        conn = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)  # autocommit
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA busy_timeout=8000;")
        except Exception:
            pass
        return conn
        
    def create_rnc(self, data: dict) -> int:
        """Criar novo RNC"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Gerar número do RNC
            rnc_number = self.generate_rnc_number()
            
            cursor.execute("""
                INSERT INTO rncs 
                (rnc_number, title, description, equipment, client, priority, status, price, user_id, department)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rnc_number,
                data.get('title', 'RNC sem título'),
                data.get('description', ''),
                data.get('equipment', ''),
                data.get('client', ''),
                data.get('priority', 'Média'),
                data.get('status', 'Pendente'),
                float(data.get('price') or 0),
                data.get('user_id', 1),
                data.get('department', '')  # Incluir o departamento/grupo
            ))
            
            rnc_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"RNC criado com sucesso: {rnc_number}")
            return rnc_id
            
        except Exception as e:
            logger.error(f"Erro ao criar RNC: {e}")
            return None
            
    def generate_rnc_number(self) -> str:
        """Gerar número único do RNC começando do 34729"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ✅ NOVA LÓGICA: Buscar MAIOR número já usado (incluindo deletadas) e incrementar
            BASE_NUMBER = 34729
            
            # Buscar o MAIOR número já usado (INCLUINDO DELETADAS para evitar conflito)
            cursor.execute("""
                SELECT rnc_number FROM rncs 
                WHERE rnc_number GLOB '[0-9]*'
                AND CAST(rnc_number AS INTEGER) >= ?
                ORDER BY CAST(rnc_number AS INTEGER) DESC 
                LIMIT 1
            """, (BASE_NUMBER,))
            
            last_rnc = cursor.fetchone()
            
            if last_rnc:
                # Pegar o último número e incrementar para evitar conflito
                try:
                    last_number = int(last_rnc[0])
                    next_number = last_number + 1
                    logger.info(f"Último número encontrado (incluindo deletadas): {last_number}, próximo será: {next_number}")
                except ValueError:
                    # Se falhar, usar base
                    next_number = BASE_NUMBER
                    logger.warning(f"Erro ao converter último número, usando base: {BASE_NUMBER}")
            else:
                # Nenhum número encontrado, começar do BASE_NUMBER
                next_number = BASE_NUMBER
                logger.info(f"Nenhum número anterior encontrado, começando em: {BASE_NUMBER}")
            
            # ✅ GARANTIR que o número não existe (nem ativo nem deletado)
            while True:
                cursor.execute('SELECT COUNT(*) FROM rncs WHERE rnc_number = ?', (str(next_number),))
                if cursor.fetchone()[0] == 0:
                    break  # Número disponível
                next_number += 1  # Incrementar se já existe
                
            conn.close()
            
            # ✅ RETORNAR APENAS O NÚMERO (sem RNC-)
            return f"{next_number}"
            
        except Exception as e:
            logger.error(f"Erro ao gerar número RNC: {e}")
            # Fallback em caso de erro
            return f"RNC-34729"
            
    def get_rnc_list(self, user_id: int = None, filters: dict = None) -> list:
        """Busca lista de RNCs considerando compartilhamentos (rnc_shares).
        Regras:
        - Admin e Ronaldo (id=5): vê todas
        - Gerentes/Subgerentes: vê todas do grupo
        - Usuário comum: vê só onde ele é causador ou criador ou compartilhadas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar informações do usuário
            user_role = None
            user_group_id = None
            manager_ids = []
            
            if user_id:
                cursor.execute("SELECT role, group_id FROM users WHERE id = ?", (user_id,))
                user_info = cursor.fetchone()
                if user_info:
                    user_role = user_info[0]
                    user_group_id = user_info[1]
                    
                    # Buscar gerentes do grupo
                    if user_group_id:
                        cursor.execute("SELECT manager_user_id, sub_manager_user_id FROM groups WHERE id = ?", (user_group_id,))
                        group_info = cursor.fetchone()
                        if group_info:
                            if group_info[0]:
                                manager_ids.append(group_info[0])
                            if group_info[1]:
                                manager_ids.append(group_info[1])
            
            # Query base
            query = """
                SELECT DISTINCT r.id, r.rnc_number, r.title, r.status, r.priority,
                                r.created_at, u.name as user_name, r.area_responsavel as department
                FROM rncs r
                LEFT JOIN users u ON r.user_id = u.id
                WHERE r.is_deleted = 0
            """
            params = []

            # FILTRO DE PERMISSÕES
            if user_id and user_role != 'admin' and user_id != 5:
                if user_id in manager_ids:
                    # Gerente/Subgerente - vê tudo do grupo
                    query += " AND r.assigned_group_id = ?"
                    params.append(user_group_id)
                else:
                    # Usuário comum - vê só dele
                    query += " AND (r.causador_user_id = ? OR r.user_id = ? OR EXISTS (SELECT 1 FROM rnc_shares rs WHERE rs.rnc_id = r.id AND rs.shared_with_user_id = ?))"
                    params.extend([user_id, user_id, user_id])
            
            # Filtros adicionais
            if filters:
                if filters.get('status'):
                    query += " AND r.status = ?"
                    params.append(filters['status'])
                    
                if filters.get('priority'):
                    query += " AND r.priority = ?"
                    params.append(filters['priority'])
                    
                if filters.get('department'):
                    query += " AND r.area_responsavel = ?"
                    params.append(filters['department'])
            
            query += " ORDER BY r.created_at DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'id': row[0],
                    'rnc_number': row[1],
                    'title': row[2],
                    'status': row[3],
                    'priority': row[4],
                    'created_at': row[5],
                    'user_name': row[6],
                    'department': row[7] if len(row) > 7 else None
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Erro ao buscar RNCs: {e}")
            return []
            
    def get_rnc_details(self, rnc_id: int) -> dict:
        """Busca detalhes completos de um RNC"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Dados principais
            cursor.execute("""
                SELECT r.*, u.name as user_name
                FROM rncs r
                LEFT JOIN users u ON r.user_id = u.id
                WHERE r.id = ?
            """, (rnc_id,))
            
            rnc_data = cursor.fetchone()
            if not rnc_data:
                return None
                
            # Detalhes técnicos
            cursor.execute("""
                SELECT * FROM rnc_details WHERE rnc_id = ?
                ORDER BY item_number
            """, (rnc_id,))
            
            details = cursor.fetchall()
            
            # Assinaturas
            cursor.execute("""
                SELECT rs.*, u.name as user_name
                FROM rnc_signatures rs
                JOIN users u ON rs.user_id = u.id
                WHERE rs.rnc_id = ?
                ORDER BY rs.signed_at
            """, (rnc_id,))
            
            signatures = cursor.fetchall()
            
            conn.close()
            
            return {
                'main': rnc_data,
                'details': details,
                'signatures': signatures
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes do RNC {rnc_id}: {e}")
            return None
            
    def update_rnc(self, rnc_id: int, data: dict) -> bool:
        """Atualizar RNC existente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE rnc_reports 
                SET title = ?, description = ?, equipment = ?, client = ?, 
                    priority = ?, status = ?, price = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('title', ''),
                data.get('description', ''),
                data.get('equipment', ''),
                data.get('client', ''),
                data.get('priority', 'Média'),
                data.get('status', 'Pendente'),
                float(data.get('price') or 0),
                rnc_id
            ))
            
            conn.commit()
            conn.close()
            
            # 🔔 Notificação Persistente: RNC Atualizada
            try:
                if notification_service:
                    change_details = {
                        'action': 'update',
                        'title': data.get('title', ''),
                        'description': data.get('description', ''),
                        'equipment': data.get('equipment', ''),
                        'client': data.get('client', ''),
                        'priority': data.get('priority', 'Média'),
                        'status': data.get('status', 'Pendente'),
                        'price': data.get('price', 0)
                    }
                    # Usar user_id = 0 como fallback, será atualizado pela API
                    notification_service.log_rnc_change(
                        rnc_id=rnc_id,
                        user_id=0,  # Será sobrescrito pela função API
                        change_type='update',
                        change_details=change_details
                    )
                    logger.info(f"✅ Notificação persistente de atualização criada para RNC {rnc_id}")
            except Exception as e:
                logger.error(f"❌ Erro ao criar notificação de atualização para RNC {rnc_id}: {e}")
            
            logger.info(f"RNC {rnc_id} atualizado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar RNC {rnc_id}: {e}")
            return False

# Instanciar sistema
rnc_system = RNCSystem(DB_PATH)

# Rotas Flask
@app.route('/')
@login_required
def dashboard():
    """Dashboard principal"""
    try:
        # Buscar RNCs do usuário atual
        user_rncs = rnc_system.get_rnc_list(user_id=current_user.id)
        
        # Estatísticas
        total_rncs = len(user_rncs)
        pending_rncs = len([r for r in user_rncs if r['status'] == 'Pendente'])
        completed_rncs = len([r for r in user_rncs if r['status'] == 'Concluído'])
        
        return render_template('dashboard.html', 
                            rncs=user_rncs[:10],  # Últimos 10
                            stats={
                                'total': total_rncs,
                                'pending': pending_rncs,
                                'completed': completed_rncs
                            })
                            
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}")
        flash('Erro ao carregar dashboard', 'error')
        return render_template('dashboard.html', rncs=[], stats={'total': 0, 'pending': 0, 'completed': 0})

@app.route('/charts-demo')
@login_required
def charts_demo():
    """Página de demonstração dos gráficos avançados"""
    return render_template('charts_demo.html')

@app.route('/dashboard-enhanced')
@login_required
def dashboard_enhanced():
    """Dashboard com gráficos avançados"""
    return render_template('dashboard_enhanced.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, email, password_hash, department, role
                FROM users WHERE email = ?
            """, (email,))
            
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data and check_password_hash(user_data[3], password):
                user = User(user_data[0], user_data[1], user_data[2], user_data[4], user_data[5])
                login_user(user)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Email ou senha incorretos', 'error')
                
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            flash('Erro interno do sistema', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/rnc/new', methods=['GET', 'POST'])
@login_required
def new_rnc():
    """Criar novo RNC"""
    if request.method == 'POST':
        try:
            data = {
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'equipment': request.form.get('equipment'),
                'client': request.form.get('client'),
                'priority': request.form.get('priority', 'Média'),
                'price': request.form.get('price'),
                'user_id': current_user.id
            }
            
            rnc_id = rnc_system.create_rnc(data)
            
            if rnc_id:
                flash('RNC criado com sucesso!', 'success')
                return redirect(url_for('view_rnc', rnc_id=rnc_id))
            else:
                flash('Erro ao criar RNC', 'error')
                
        except Exception as e:
            logger.error(f"Erro ao criar RNC: {e}")
            flash('Erro interno do sistema', 'error')
    
    # GET: renderizar formulário já com lista de clientes
    try:
        ensure_clients_table()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT name FROM clients ORDER BY name')
        clients = [row[0] for row in cur.fetchall()]
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao carregar clientes para novo RNC: {e}")
        clients = []
    return render_template('new_rnc.html', clients=clients)

@app.route('/rnc/<int:rnc_id>')
@login_required
def view_rnc(rnc_id):
    """Visualizar RNC específico"""
    try:
        rnc_details = rnc_system.get_rnc_details(rnc_id)
        
        if not rnc_details:
            flash('RNC não encontrado', 'error')
            return redirect(url_for('dashboard'))
            
        # Verificar se o usuário tem acesso a este RNC (criador, admin ou compartilhado)
        is_owner = (rnc_details['main'][9] == current_user.id)
        is_admin = (current_user.role == 'admin')
        has_share = False
        if not (is_owner or is_admin):
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute('SELECT 1 FROM rnc_shares WHERE rnc_id = ? AND shared_with_user_id = ? LIMIT 1', (rnc_id, current_user.id))
                has_share = cur.fetchone() is not None
                conn.close()
            except Exception as ie:
                logger.error(f"Erro ao verificar compartilhamento da RNC {rnc_id}: {ie}")
        if not (is_owner or is_admin or has_share):
            flash('Acesso negado', 'error')
            return redirect(url_for('dashboard'))
            
        return render_template('view_rnc.html', rnc=rnc_details)
        
    except Exception as e:
        logger.error(f"Erro ao visualizar RNC {rnc_id}: {e}")
        flash('Erro interno do sistema', 'error')
        return redirect(url_for('dashboard'))

@app.route('/rnc/list')
@login_required
def list_rncs():
    """Listar todos os RNCs do usuário"""
    try:
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('priority'):
            filters['priority'] = request.args.get('priority')
            
        rncs = rnc_system.get_rnc_list(user_id=current_user.id, filters=filters)
        return render_template('list_rncs.html', rncs=rncs)
        
    except Exception as e:
        logger.error(f"Erro ao listar RNCs: {e}")
        flash('Erro interno do sistema', 'error')
        return render_template('list_rncs.html', rncs=[])

# APIs para integração com formulário
@app.route('/api/rnc/create', methods=['POST'])
def create_rnc_from_form():
    """API para criar RNC a partir do formulário index.html"""
    try:
        data = request.get_json()
        
        # Verificar se usuário está logado
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'Usuário não autenticado'
            }), 401
        
        # Processar grupos selecionados para obter o departamento
        shared_group_ids = data.get('shared_group_ids', [])
        department = ''
        
        if shared_group_ids:
            # Conectar ao banco para buscar o nome do grupo selecionado
            try:
                conn = sqlite3.connect('ippel_system.db')
                cursor = conn.cursor()
                
                # Buscar nome do primeiro grupo selecionado pela tabela groups
                for group_id in shared_group_ids:
                    if group_id and str(group_id).isdigit():
                        cursor.execute("SELECT name FROM groups WHERE id = ?", (group_id,))
                        result = cursor.fetchone()
                        if result and result[0]:
                            department = result[0]
                            break
                conn.close()
                
            except Exception as e:
                logger.error(f"Erro ao processar grupos: {e}")
                department = ''
        
        # Fallback: se ainda vazio, usar primeiro grupo como texto (caso frontend envie nomes futuramente)
        if not department and shared_group_ids:
            department = str(shared_group_ids[0])
        
        # Extrair dados do formulário
        rnc_data = {
            'title': data.get('title', 'RNC sem título'),
            'description': data.get('description', ''),
            'equipment': data.get('equipment', ''),
            'client': data.get('client', ''),
            'priority': data.get('priority', 'Média'),
            'status': 'Pendente',
            'price': data.get('price', 0),
            'user_id': current_user.id,
            'department': department  # Incluir o departamento dos grupos selecionados
        }
        
        # Log para debug
        logger.info(f"Criando RNC - Usuário: {current_user.username}, Grupos selecionados: {shared_group_ids}, Departamento atribuído: {department}")
        
        # Criar RNC no sistema
        rnc_id = rnc_system.create_rnc(rnc_data)
        
        if rnc_id:
            # 🔔 NOTIFICAÇÃO PERSISTENTE: Nova RNC Criada
            try:
                from services.persistent_notifications_service import PersistentNotificationService
                notification_service = PersistentNotificationService()
                
                change_details = {
                    'action': 'create',
                    'user': current_user.username,
                    'title': rnc_data.get('title', ''),
                    'description': rnc_data.get('description', ''),
                    'equipment': rnc_data.get('equipment', ''),
                    'client': rnc_data.get('client', ''),
                    'priority': rnc_data.get('priority', 'Média'),
                    'department': department,
                    'groups_shared': shared_group_ids
                }
                notification_service.log_rnc_change(
                    rnc_id=rnc_id,
                    user_id=current_user.id,
                    change_type='create',
                    change_details=change_details
                )
                logger.info(f"✅ Notificação persistente de criação criada para RNC {rnc_id} por {current_user.username}")
            except Exception as e:
                logger.error(f"❌ Erro ao criar notificação de criação para RNC {rnc_id}: {e}")
            
            # Buscar dados do RNC criado
            rnc_details = rnc_system.get_rnc_details(rnc_id)
            
            # Registrar compartilhamentos explícitos para usuários dos grupos selecionados
            try:
                if shared_group_ids:
                    import time
                    conn = rnc_system._get_conn()
                    cursor = conn.cursor()
                    total_shared = 0

                    # Causador (se informado) + gerente + subgerente + Ronaldo (ID 5) + criador (já possui via user_id)
                    causador_user_id = data.get('causador_user_id')
                    try:
                        if causador_user_id:
                            causador_user_id = int(str(causador_user_id).strip())
                        else:
                            causador_user_id = None
                    except ValueError:
                        causador_user_id = None

                    allowed_extra_users = set()
                    if causador_user_id and causador_user_id != current_user.id:
                        allowed_extra_users.add(causador_user_id)
                    # Ronaldo (id fixo 5) – confirmar se existe no sistema
                    allowed_extra_users.add(5)

                    for group_id in shared_group_ids:
                        if not group_id:
                            continue
                        if str(group_id).isdigit():
                            cursor.execute("SELECT manager_user_id, sub_manager_user_id FROM groups WHERE id = ?", (group_id,))
                            mg = cursor.fetchone()
                            if mg:
                                m_id, sm_id = mg
                                if m_id and m_id != current_user.id:
                                    allowed_extra_users.add(m_id)
                                if sm_id and sm_id != current_user.id:
                                    allowed_extra_users.add(sm_id)

                    # Inserir compartilhamentos SOMENTE para usuários permitidos
                    for uid in allowed_extra_users:
                        if not uid or uid == current_user.id:
                            continue
                        for attempt in range(5):
                            try:
                                cursor.execute("""
                                    INSERT OR IGNORE INTO rnc_shares (rnc_id, shared_by_user_id, shared_with_user_id, permission_level)
                                    VALUES (?, ?, ?, 'view')
                                """, (rnc_id, current_user.id, uid))
                                total_shared += 1
                                break
                            except sqlite3.OperationalError as ex:
                                if 'locked' in str(ex).lower() and attempt < 4:
                                    time.sleep(0.3 * (attempt + 1))
                                    continue
                                else:
                                    raise

                    conn.commit(); conn.close()
                    logger.info(f"RNC {rnc_id} compartilhada com {total_shared} usuários permitidos (causador/gestores/Ronaldo). groups={shared_group_ids} dept={department} causador={causador_user_id}")
            except Exception as e:
                logger.error(f"Falha ao registrar compartilhamentos da RNC {rnc_id}: {e}")
            
            # 🔔 Notificação Persistente: RNC Criada
            try:
                if notification_service:
                    change_details = {
                        'action': 'create',
                        'title': rnc_data['title'],
                        'description': rnc_data['description'],
                        'priority': rnc_data['priority'],
                        'department': department,
                        'shared_groups': shared_group_ids
                    }
                    notification_service.log_rnc_change(
                        rnc_id=rnc_id,
                        user_id=current_user.id,
                        change_type='create',
                        change_details=change_details
                    )
                    logger.info(f"✅ Notificação persistente criada para RNC {rnc_id}")
                else:
                    logger.warning("⚠️ Serviço de notificações persistentes não disponível")
            except Exception as e:
                logger.error(f"❌ Erro ao criar notificação persistente para RNC {rnc_id}: {e}")
            
            return jsonify({
                'success': True,
                'message': 'RNC criado com sucesso!',
                'rnc_id': rnc_id,
                'rnc_number': rnc_details['main'][1] if rnc_details else None,
                'redirect_url': f'/rnc/{rnc_id}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erro ao criar RNC'
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao criar RNC via API: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@app.route('/api/rnc/<int:rnc_id>/details')
@login_required
def get_rnc_details_api(rnc_id):
    """API para obter detalhes de um RNC"""
    try:
        rnc_details = rnc_system.get_rnc_details(rnc_id)
        
        if rnc_details:
            # Verificar acesso (criador, admin ou compartilhado)
            is_owner = (rnc_details['main'][9] == current_user.id)
            is_admin = (current_user.role == 'admin')
            has_share = False
            if not (is_owner or is_admin):
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    cur.execute('SELECT 1 FROM rnc_shares WHERE rnc_id = ? AND shared_with_user_id = ? LIMIT 1', (rnc_id, current_user.id))
                    has_share = cur.fetchone() is not None
                    conn.close()
                except Exception as ie:
                    logger.error(f"Erro ao verificar compartilhamento da RNC {rnc_id}: {ie}")
            if not (is_owner or is_admin or has_share):
                return jsonify({'success': False, 'message': 'Acesso negado'}), 403
                
            return jsonify({
                'success': True,
                'rnc': rnc_details
            })
        else:
            return jsonify({
                'success': False,
                'message': 'RNC não encontrado'
            }), 404
            
    except Exception as e:
        logger.error(f"Erro ao buscar RNC {rnc_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@app.route('/api/rnc/list')
def get_rnc_list_api():
    """API para listar RNCs do usuário com paginação eficiente"""
    try:
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'Usuário não autenticado'
            }), 401
        
        # Parâmetros de paginação
        tab = request.args.get('tab', 'active')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 30))
        offset = (page - 1) * limit
        
        # Parâmetros de filtro
        search = request.args.get('search', '').strip()
        client = request.args.get('client', '').strip()
        department = request.args.get('department', '').strip()
        responsible = request.args.get('responsible', '').strip()
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Buscar informações do usuário atual
        cursor.execute('SELECT role, group_id FROM users WHERE id = ?', (current_user.id,))
        user_info = cursor.fetchone()
        user_role = user_info['role'] if user_info else None
        user_group_id = user_info['group_id'] if user_info else None
        
        # Buscar gerentes e subgerentes do grupo do usuário
        manager_ids = []
        if user_group_id:
            cursor.execute('SELECT manager_user_id, sub_manager_user_id FROM groups WHERE id = ?', (user_group_id,))
            group_info = cursor.fetchone()
            if group_info:
                if group_info['manager_user_id']:
                    manager_ids.append(group_info['manager_user_id'])
                if group_info['sub_manager_user_id']:
                    manager_ids.append(group_info['sub_manager_user_id'])
        
        # Base query otimizada com índices
        base_where = ["r.is_deleted = 0"]
        params = []
        
        # Filtro por aba
        if tab == 'finalized':
            base_where.append("r.status = 'Finalizado'")
        else:  # active
            base_where.append("r.status != 'Finalizado'")
        
        # FILTRO DE PERMISSÕES
        # Admin vê tudo, Ronaldo (id=5) vê tudo
        logger.info(f"[FILTRO] User ID: {current_user.id}, Role: {user_role}, Group: {user_group_id}, Managers: {manager_ids}")
        
        if user_role != 'admin' and current_user.id != 5:
            # Usuários comuns vêem apenas:
            # 1. RNCs compartilhadas com ele (rnc_shares)
            # 2. RNCs onde ele é o causador (causador_user_id)
            # Gerentes/subgerentes vêem tudo do grupo
            if current_user.id in manager_ids:
                # É gerente ou subgerente - vê tudo do grupo
                logger.info(f"[FILTRO] Usuário é GERENTE/SUBGERENTE - vendo tudo do grupo {user_group_id}")
                base_where.append("r.assigned_group_id = ?")
                params.append(user_group_id)
            else:
                # Usuário comum - vê só as dele
                logger.info(f"[FILTRO] Usuário COMUM - vendo só suas RNCs (causador={current_user.id})")
                base_where.append("(r.causador_user_id = ? OR r.user_id = ? OR EXISTS (SELECT 1 FROM rnc_shares rs WHERE rs.rnc_id = r.id AND rs.shared_with_user_id = ?))")
                params.extend([current_user.id, current_user.id, current_user.id])
        else:
            logger.info(f"[FILTRO] Admin ou Ronaldo - vendo TODAS as RNCs")
        
        # Filtros adicionais
        if search:
            base_where.append("(r.rnc_number LIKE ? OR r.title LIKE ? OR r.description LIKE ?)")
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        if client:
            base_where.append("r.client = ?")
            params.append(client)
        
        if department:
            base_where.append("r.area_responsavel = ?")
            params.append(department)
        
        if responsible:
            base_where.append("r.responsavel = ?")
            params.append(responsible)
        
        where_clause = " AND ".join(base_where)
        
        # Log da query para debug
        logger.info(f"[QUERY] WHERE: {where_clause}")
        logger.info(f"[QUERY] PARAMS: {params}")
        
        # Contar total (com cache para performance)
        count_query = f"SELECT COUNT(*) as total FROM rncs r WHERE {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Query principal com LIMIT e OFFSET
        query = f"""
            SELECT 
                r.id, r.rnc_number, r.title, r.description, r.status, r.priority,
                r.client, r.equipment, r.drawing, r.revision, r.conjunto,
                r.description_drawing, r.position, r.modelo, r.material, r.quantity,
                r.cv, r.mp, r.price, r.area_responsavel, r.responsavel,
                r.inspetor, r.created_at, r.finalized_at, r.updated_at,
                u.name as user_name
            FROM rncs r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE {where_clause}
            ORDER BY r.created_at DESC
            LIMIT ? OFFSET ?
        """
        
        params.extend([limit, offset])
        cursor.execute(query, params)
        
        rncs = []
        for row in cursor.fetchall():
            rncs.append({
                'id': row['id'],
                'rnc_number': row['rnc_number'],
                'title': row['title'],
                'description': row['description'],
                'status': row['status'],
                'priority': row['priority'],
                'client': row['client'],
                'equipment': row['equipment'],
                'drawing': row['drawing'],
                'revision': row['revision'],
                'conjunto': row['conjunto'],
                'description_drawing': row['description_drawing'],
                'position': row['position'],
                'modelo': row['modelo'],
                'material': row['material'],
                'quantity': row['quantity'],
                'cv': row['cv'],
                'mp': row['mp'],
                'price': row['price'],
                'area_responsavel': row['area_responsavel'],
                'responsavel': row['responsavel'],
                'inspetor': row['inspetor'],
                'created_at': row['created_at'],
                'finalized_at': row['finalized_at'],
                'updated_at': row['updated_at'],
                'user_name': row['user_name']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'rncs': rncs,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar RNCs: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500


@app.route('/api/rnc/random')
def get_random_rnc_api():
    """API para buscar uma RNC aleatória"""
    try:
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'Usuário não autenticado'
            }), 401
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Buscar uma RNC aleatória do banco
        cursor.execute("""
            SELECT id, titulo_rnc, descricao, equipamento_sistema, cliente_departamento,
                   mp, revisao, posicao, cv, conjunto, modelo, descricao_desenho,
                   quantidade, material, ordem_compra, responsavel_deteccao, inspetor,
                   area_setor, instrucao_retrabalho, analise_causa_raiz, plano_acao,
                   nivel_urgencia, custo_estimado, created_at
            FROM rncs 
            ORDER BY RANDOM() 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            rnc_data = {
                'id': row[0],
                'titulo_rnc': row[1] or '',
                'descricao': row[2] or '',
                'equipamento_sistema': row[3] or '',
                'cliente_departamento': row[4] or '',
                'mp': row[5] or '',
                'revisao': row[6] or '',
                'posicao': row[7] or '',
                'cv': row[8] or '',
                'conjunto': row[9] or '',
                'modelo': row[10] or '',
                'descricao_desenho': row[11] or '',
                'quantidade': row[12] or '',
                'material': row[13] or '',
                'ordem_compra': row[14] or '',
                'responsavel_deteccao': row[15] or '',
                'inspetor': row[16] or '',
                'area_setor': row[17] or '',
                'instrucao_retrabalho': row[18] or '',
                'analise_causa_raiz': row[19] or '',
                'plano_acao': row[20] or '',
                'nivel_urgencia': row[21] or '',
                'custo_estimado': row[22] or '',
                'created_at': row[23] or ''
            }
            
            return jsonify({
                'success': True,
                'rnc': rnc_data,
                'message': f'RNC #{rnc_data["id"]} carregada com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Nenhuma RNC encontrada no banco de dados'
            }), 404
            
    except Exception as e:
        logger.error(f"Erro ao buscar RNC aleatória: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500


@app.route('/api/clients/import', methods=['POST'])
def import_clients_from_rnc_data():
    """API para importar clientes dos dados RNC"""
    try:
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'Usuário não autenticado'
            }), 401
        
        # Verificar se usuário é admin
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Acesso negado. Apenas administradores podem importar clientes.'
            }), 403
        
        # Ler dados do arquivo
        file_path = os.path.join(os.path.dirname(__file__), 'DADOS PUXAR RNC', 'DADOS PUXAR RNC.txt')
        logger.info(f"Tentando ler arquivo: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            return jsonify({
                'success': False,
                'message': f'Arquivo de dados não encontrado: {file_path}'
            }), 404
        
        clients_set = set()
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
            
            # Pular o cabeçalho
            for line in lines[1:]:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 12:  # Verificar se tem colunas suficientes
                        cliente = parts[11].strip()  # Coluna CLIENTE
                        if cliente and cliente != 'CLIENTE' and len(cliente) > 1:
                            # Limpar o nome do cliente
                            cliente = ' '.join(cliente.split())
                            if cliente:
                                clients_set.add(cliente)
        
        # Conectar ao banco e inserir clientes
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                contact_info TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        inserted_count = 0
        updated_count = 0
        
        clients_list = sorted(list(clients_set))
        
        for client_name in clients_list:
            try:
                # Verificar se cliente já existe
                cursor.execute("SELECT id FROM clients WHERE name = ?", (client_name,))
                existing = cursor.fetchone()
                
                if existing:
                    # Atualizar cliente existente
                    cursor.execute("""
                        UPDATE clients 
                        SET updated_at = CURRENT_TIMESTAMP,
                            active = 1
                        WHERE name = ?
                    """, (client_name,))
                    updated_count += 1
                else:
                    # Inserir novo cliente
                    cursor.execute("""
                        INSERT INTO clients (name, description, active, created_at, updated_at)
                        VALUES (?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (client_name, f"Cliente importado dos dados RNC"))
                    inserted_count += 1
                    
            except sqlite3.IntegrityError:
                continue  # Cliente já existe
            except Exception as e:
                logger.error(f"Erro ao inserir cliente '{client_name}': {e}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Importação concluída! {inserted_count} novos clientes inseridos, {updated_count} atualizados.',
            'inserted': inserted_count,
            'updated': updated_count,
            'total_found': len(clients_list),
            'clients': clients_list[:10]  # Retornar apenas os primeiros 10 para preview
        })
        
    except Exception as e:
        logger.error(f"Erro ao importar clientes: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500


@app.route('/api/clients', methods=['GET'])
def get_clients_api():
    """API para listar todos os clientes"""
    try:
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'Usuário não autenticado'
            }), 401
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, contact_info, active, created_at, updated_at
            FROM clients 
            WHERE active = 1
            ORDER BY name
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        clients = []
        for row in rows:
            clients.append({
                'id': row[0],
                'name': row[1],
                'description': row[2] or '',
                'contact_info': row[3] or '',
                'active': bool(row[4]),
                'created_at': row[5],
                'updated_at': row[6]
            })
        
        return jsonify({
            'success': True,
            'clients': clients,
            'total': len(clients)
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar clientes: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500


@app.route('/api/admin/groups', methods=['GET'])
def api_get_groups():
    """Retornar lista de grupos para seleção no formulário.
    Acesso: qualquer usuário autenticado. Mantém o formato esperado pelo index.html
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description FROM groups ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        groups_list = [
            {
                'id': row[0],
                'name': row[1],
                'description': row[2] or '',
                'user_count': 0
            }
            for row in rows
        ]

        return jsonify({'success': True, 'groups': groups_list})
    except Exception as e:
        logger.error(f"Erro ao listar grupos: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do sistema'}), 500


@app.route('/api/groups', methods=['GET'])
def api_get_groups_simple():
    """Endpoint simplificado para listar setores das RNCs"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Buscar setores únicos das RNCs (setor e area_responsavel)
        cursor.execute("""
            SELECT DISTINCT setor FROM rncs 
            WHERE setor IS NOT NULL AND setor != '' AND is_deleted = 0
            UNION
            SELECT DISTINCT area_responsavel FROM rncs 
            WHERE area_responsavel IS NOT NULL 
            AND area_responsavel != '' 
            AND is_deleted = 0
            AND CAST(area_responsavel AS TEXT) NOT GLOB '[0-9]*'
            ORDER BY 1
        """)
        rows = cursor.fetchall()
        conn.close()

        groups_list = [{'name': row[0]} for row in rows if row[0]]

        return jsonify(groups_list)  # Retorna array diretamente para compatibilidade com frontend
    except Exception as e:
        logger.error(f"Erro ao listar setores: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do sistema'}), 500


@app.route('/api/users', methods=['GET'])
def api_get_users():
    """Endpoint para listar usuários (operators)"""
    try:
        if not current_user.is_authenticated:
            logger.warning("Tentativa de acesso não autenticado ao /api/users")
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401

        logger.info(f"Usuário {current_user.id} acessando /api/users")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se a tabela operators existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operators'")
        if not cursor.fetchone():
            logger.error("Tabela 'operators' não encontrada no banco de dados")
            conn.close()
            return jsonify({'success': False, 'message': 'Tabela de usuários não encontrada'}), 500
        
        cursor.execute("""
            SELECT o.id, o.name, o.number, o.group_id, g.name as group_name
            FROM operators o
            LEFT JOIN groups g ON o.group_id = g.id
            WHERE o.is_active = 1
            ORDER BY o.name
        """)
        rows = cursor.fetchall()
        conn.close()

        logger.info(f"Encontrados {len(rows)} usuários ativos")

        users_list = [
            {
                'id': row[0],
                'name': row[1] or '',
                'number': row[2] or '',
                'username': row[1] or '',  # usando name como username
                'group_id': row[3],
                'group_name': row[4] or 'Sem grupo'
            }
            for row in rows
        ]

        return jsonify(users_list)  # Retorna array diretamente para compatibilidade com frontend
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {e}")
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500


@app.route('/api/logout')
def api_logout():
    """Logout via API, usado pelo formulário público."""
    try:
        if current_user.is_authenticated:
            logout_user()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erro no logout: {e}")
        return jsonify({'success': False, 'message': 'Erro ao fazer logout'}), 500

@app.route('/api/user/info')
def get_user_info():
    """API para obter informações do usuário logado"""
    try:
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'Usuário não autenticado'
            }), 401
            
        return jsonify({
            'success': True,
            'user': {
                'id': current_user.id,
                'name': current_user.name,
                'email': current_user.email,
                'department': current_user.department,
                'role': current_user.role
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter informações do usuário: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@app.route('/api/admin/groups', methods=['GET'])
def api_admin_groups():
    """Retorna lista de grupos para seleção no formulário.
    Qualquer usuário autenticado pode listar grupos (não exige permissão admin)."""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description FROM groups ORDER BY name")
        rows = cursor.fetchall()

        groups_list = []
        for row in rows:
            group_id, group_name, description = row
            # Estimar número de usuários pelo campo department
            cursor.execute("SELECT COUNT(*) FROM users WHERE department = ?", (group_name,))
            count = cursor.fetchone()[0]
            groups_list.append({
                'id': group_id,
                'name': group_name,
                'description': description or '',
                'user_count': count
            })

        conn.close()
        return jsonify({'success': True, 'groups': groups_list})
    except Exception as e:
        logger.error(f"Erro ao listar grupos: {e}")
        return jsonify({'success': False, 'message': 'Erro interno ao listar grupos'}), 500

@app.route('/api/charts/enhanced-data')
def api_charts_enhanced_data():
    """Endpoint para dados dos gráficos aprimorados com dados reais da planilha de indicadores"""
    try:
        period = request.args.get('period', '30')
        department = request.args.get('department', 'all')
        # Tentar carregar dados reais da planilha de indicadores
        import json
        import os
        from pathlib import Path
        # Prefer JSON files under data/ quando presente para manter a raiz limpa
        _ROOT = Path(__file__).resolve().parent
        _DATA_DIR = _ROOT / 'data'
        api_data_file = str((_DATA_DIR / 'api_chart_data.json') if (_DATA_DIR / 'api_chart_data.json').exists() else (_ROOT / 'api_chart_data.json'))
        if os.path.exists(api_data_file):
            try:
                with open(api_data_file, 'r', encoding='utf-8') as f:
                    real_data = json.load(f)
                
                # Se os dados foram carregados com sucesso, usar dados reais
                if real_data.get('success'):
                    logger.info("Usando dados reais da planilha de indicadores")
                    
                    # Enriquecer com dados adicionais para os gráficos
                    chart_data = real_data['data'].copy()
                    
                    # Adicionar dados de tendência simulados baseados nos dados reais
                    chart_data['trend'] = [
                        {'date': '2025-08-01', 'count': 12},
                        {'date': '2025-08-02', 'count': 8},
                        {'date': '2025-08-03', 'count': 15},
                        {'date': '2025-08-04', 'count': 6},
                        {'date': '2025-08-05', 'count': 18},
                        {'date': '2025-08-06', 'count': 11},
                        {'date': '2025-08-07', 'count': 9}
                    ]
                    
                    # Adicionar dados de status baseados nos departamentos
                    total_rncs = sum(dept['count'] for dept in chart_data.get('departments', []))
                    chart_data['status'] = [
                        {'label': 'Aberta', 'count': int(total_rncs * 0.3), 'color': '#ff6b6b'},
                        {'label': 'Em Análise', 'count': int(total_rncs * 0.25), 'color': '#4ecdc4'},
                        {'label': 'Aguardando', 'count': int(total_rncs * 0.15), 'color': '#45b7d1'},
                        {'label': 'Finalizada', 'count': int(total_rncs * 0.3), 'color': '#96ceb4'}
                    ]
                    
                    # Adicionar dados de prioridade
                    chart_data['priority'] = [
                        {'label': 'Baixa', 'count': int(total_rncs * 0.4), 'color': '#4ade80'},
                        {'label': 'Média', 'count': int(total_rncs * 0.35), 'color': '#fbbf24'},
                        {'label': 'Alta', 'count': int(total_rncs * 0.2), 'color': '#f97316'},
                        {'label': 'Crítica', 'count': int(total_rncs * 0.05), 'color': '#ef4444'}
                    ]
                    
                    # Adicionar dados para outros gráficos
                    chart_data.update({
                        'area': {
                            'dates': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
                            'datasets': [
                                {'label': 'Abertas', 'data': [20, 25, 18, 30, 22, 28]},
                                {'label': 'Em Análise', 'data': [15, 20, 12, 25, 18, 22]},
                                {'label': 'Finalizadas', 'data': [35, 40, 30, 45, 38, 42]}
                            ]
                        },
                        'scatter': {
                            'data': [
                                {'x': 1, 'y': 5}, {'x': 2, 'y': 8}, {'x': 3, 'y': 12}, {'x': 4, 'y': 15},
                                {'x': 1, 'y': 3}, {'x': 2, 'y': 6}, {'x': 3, 'y': 9}, {'x': 4, 'y': 18}
                            ]
                        },
                        'stacked': {
                            'labels': ['Engenharia', 'Produção', 'Suprimentos', 'PCP'],
                            'datasets': [
                                {'label': 'Abertas', 'data': [12, 8, 15, 6]},
                                {'label': 'Em Análise', 'data': [8, 12, 10, 4]},
                                {'label': 'Finalizadas', 'data': [25, 18, 22, 12]}
                            ]
                        },
                        'heatmap': []
                    })
                    
                    # Gerar dados do heatmap
                    for day in range(7):
                        for hour in range(24):
                            chart_data['heatmap'].append({
                                'x': hour,
                                'y': day, 
                                'v': random.randint(1, 15)
                            })
                    
                    return jsonify({'success': True, 'data': chart_data})
                    
            except Exception as e:
                logger.warning(f"Erro ao carregar dados da planilha: {e}")
        
        # Fallback para dados simulados se não conseguir carregar dados reais
        logger.info("Usando dados simulados - planilha não disponível")
        
        # Dados simulados realistas baseados no banco
        data = {
            'trend': [
                {'date': '2025-08-01', 'count': 12},
                {'date': '2025-08-02', 'count': 8},
                {'date': '2025-08-03', 'count': 15},
                {'date': '2025-08-04', 'count': 6},
                {'date': '2025-08-05', 'count': 18},
                {'date': '2025-08-06', 'count': 11},
                {'date': '2025-08-07', 'count': 9}
            ],
            'status': [
                {'label': 'Aberta', 'count': 125, 'color': '#ff6b6b'},
                {'label': 'Em Análise', 'count': 89, 'color': '#4ecdc4'},
                {'label': 'Aguardando', 'count': 34, 'color': '#45b7d1'},
                {'label': 'Finalizada', 'count': 342, 'color': '#96ceb4'}
            ],
            'priority': [
                {'label': 'Baixa', 'count': 180, 'color': '#4ade80'},
                {'label': 'Média', 'count': 250, 'color': '#fbbf24'},
                {'label': 'Alta', 'count': 120, 'color': '#f97316'},
                {'label': 'Crítica', 'count': 40, 'color': '#ef4444'}
            ],
            'users': [
                {'label': 'João Silva', 'count': 25},
                {'label': 'Maria Santos', 'count': 18},
                {'label': 'Carlos Lima', 'count': 22},
                {'label': 'Ana Costa', 'count': 15},
                {'label': 'Pedro Rocha', 'count': 12}
            ],
            'equipment': [
                {'label': 'Torno CNC', 'count': 8},
                {'label': 'Prensa Hidráulica', 'count': 12},
                {'label': 'Soldadora MIG', 'count': 6},
                {'label': 'Compressor', 'count': 9},
                {'label': 'Fresa', 'count': 7}
            ],
            'kpis': {'total': 590, 'resolved': 512},
            'departments': [
                {'label': 'Produção', 'count': 45, 'efficiency': 85},
                {'label': 'Qualidade', 'count': 32, 'efficiency': 92},
                {'label': 'Manutenção', 'count': 28, 'efficiency': 78},
                {'label': 'Comercial', 'count': 15, 'efficiency': 95}
            ],
            'heatmap': [],
            'area': {
                'dates': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
                'datasets': [
                    {'label': 'Abertas', 'data': [20, 25, 18, 30, 22, 28]},
                    {'label': 'Em Análise', 'data': [15, 20, 12, 25, 18, 22]},
                    {'label': 'Finalizadas', 'data': [35, 40, 30, 45, 38, 42]}
                ]
            },
            'scatter': {
                'data': [
                    {'x': 1, 'y': 5}, {'x': 2, 'y': 8}, {'x': 3, 'y': 12}, {'x': 4, 'y': 15},
                    {'x': 1, 'y': 3}, {'x': 2, 'y': 6}, {'x': 3, 'y': 9}, {'x': 4, 'y': 18}
                ]
            },
            'stacked': {
                'labels': ['Produção', 'Qualidade', 'Manutenção', 'Comercial'],
                'datasets': [
                    {'label': 'Abertas', 'data': [12, 8, 15, 6]},
                    {'label': 'Em Análise', 'data': [8, 12, 10, 4]},
                    {'label': 'Finalizadas', 'data': [25, 18, 22, 12]}
                ]
            }
        }
        
        # Gerar dados do heatmap
        for day in range(7):
            for hour in range(24):
                data['heatmap'].append({
                    'x': hour,
                    'y': day, 
                    'v': random.randint(1, 20)
                })
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        logger.error(f"Erro ao gerar dados dos gráficos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/dashboard/api/kpis')
def api_kpis():
    """Endpoint para KPIs do dashboard"""
    try:
        return jsonify({
            'total': 2856,
            'avgTime': '7.2',
            'resolution': 87,
            'efficiency': 92,
            'totalChange': 12,
            'avgTimeChange': -8,
            'resolutionChange': 5,
            'efficiencyChange': 3
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/test_charts')
def test_charts():
    """Página de teste dos gráficos"""
    return send_from_directory('.', 'test_charts.html')

@app.route('/rnc/<int:rnc_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rnc(rnc_id):
    """Editar RNC existente"""
    try:
        rnc_details = rnc_system.get_rnc_details(rnc_id)
        
        if not rnc_details:
            flash('RNC não encontrado', 'error')
            return redirect(url_for('dashboard'))
            
        # Verificar se o usuário tem acesso a este RNC
        if rnc_details['main'][9] != current_user.id and current_user.role != 'admin':
            flash('Acesso negado', 'error')
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            # Processar formulário de edição
            data = {
                'title': request.form.get('title', ''),
                'description': request.form.get('description', ''),
                'equipment': request.form.get('equipment', ''),
                'client': request.form.get('client', ''),
                'priority': request.form.get('priority', 'Média'),
                'status': request.form.get('status', 'Pendente'),
                'price': request.form.get('price')
            }
            
            if rnc_system.update_rnc(rnc_id, data):
                flash('RNC atualizado com sucesso!', 'success')
                return redirect(url_for('view_rnc', rnc_id=rnc_id))
            else:
                flash('Erro ao atualizar RNC', 'error')
                
        return render_template('edit_rnc.html', rnc=rnc_details)
        
    except Exception as e:
        logger.error(f"Erro ao editar RNC {rnc_id}: {e}")
        flash('Erro interno do sistema', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/rnc/<int:rnc_id>/update', methods=['PUT'])
@login_required
def update_rnc_api(rnc_id):
    """API para atualizar RNC"""
    try:
        rnc_details = rnc_system.get_rnc_details(rnc_id)
        
        if not rnc_details:
            return jsonify({
                'success': False,
                'message': 'RNC não encontrado'
            }), 404
            
        # Verificar acesso
        if rnc_details['main'][9] != current_user.id and current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': 'Acesso negado'
            }), 403
            
        data = request.get_json()
        
        if rnc_system.update_rnc(rnc_id, data):
            # 🔔 NOTIFICAÇÃO PERSISTENTE: RNC Atualizada
            try:
                from services.persistent_notifications_service import PersistentNotificationService
                notification_service = PersistentNotificationService()
                
                change_details = {
                    'action': 'update_api',
                    'user': current_user.username,
                    'title': data.get('title', ''),
                    'description': data.get('description', ''),
                    'equipment': data.get('equipment', ''),
                    'client': data.get('client', ''),
                    'priority': data.get('priority', 'Média'),
                    'status': data.get('status', 'Pendente'),
                    'price': data.get('price', 0)
                }
                notification_service.log_rnc_change(
                    rnc_id=rnc_id,
                    user_id=current_user.id,
                    change_type='update',
                    change_details=change_details
                )
                logger.info(f"✅ Notificação persistente de atualização criada para RNC {rnc_id} por {current_user.username}")
            except Exception as e:
                logger.error(f"❌ Erro ao criar notificação de atualização para RNC {rnc_id}: {e}")
                
            return jsonify({
                'success': True,
                'message': 'RNC atualizado com sucesso!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erro ao atualizar RNC'
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao atualizar RNC {rnc_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

# Endpoint para deletar RNC
@app.route('/api/rnc/<int:rnc_id>/delete', methods=['DELETE'])
@login_required
def delete_rnc(rnc_id):
    """Deleta uma RNC definitivamente"""
    try:
        logger.info(f"🗑️ Tentativa de exclusão da RNC {rnc_id} pelo usuário {current_user.email}")
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Verificar se a RNC existe (usando tabela correta 'rncs')
        cur.execute('SELECT id, rnc_number FROM rncs WHERE id = ?', (rnc_id,))
        rnc = cur.fetchone()
        
        if not rnc:
            conn.close()
            logger.warning(f"❌ RNC {rnc_id} não encontrada para exclusão")
            return jsonify({
                'success': False,
                'message': 'RNC não encontrada'
            }), 404
        
        rnc_number = rnc[1]
        
        # Deletar a RNC da tabela correta
        cur.execute('DELETE FROM rncs WHERE id = ?', (rnc_id,))
        rnc_deleted = cur.rowcount
        
        if rnc_deleted == 0:
            conn.rollback()
            conn.close()
            logger.error(f"❌ Falha ao deletar RNC {rnc_id}")
            return jsonify({
                'success': False,
                'message': 'Erro ao deletar RNC'
            }), 500
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ RNC {rnc_number} (ID: {rnc_id}) deletada com sucesso da tabela 'rncs'")
        
        return jsonify({
            'success': True,
            'message': f'RNC {rnc_number} deletada com sucesso',
            'deleted_rnc_id': rnc_id,
            'deleted_rnc_number': rnc_number
        })
        
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        logger.error(f"❌ Erro de banco de dados ao deletar RNC {rnc_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro no banco de dados: {str(e)}'
        }), 500
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        logger.error(f"❌ Erro interno ao deletar RNC {rnc_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

# Lista de clientes para uso geral (formulários). Requer usuário autenticado.
@app.route('/api/clients', methods=['GET'])
@login_required
def api_clients_public():
    try:
        ensure_clients_table()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT name FROM clients ORDER BY name')
        names = [row[0] for row in cur.fetchall()]
        conn.close()
        return jsonify({'success': True, 'clients': names})
    except Exception as e:
        logger.error(f"Erro ao listar clientes: {e}")
        try:
            conn.close()
        except Exception:
            pass
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500

# Endpoint de teste para debug de grupos
@app.route('/api/test/groups-debug')
@login_required
def test_groups_debug():
    """Endpoint para debug do sistema de grupos"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Informações do usuário atual
        user_info = {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email,
            'department': current_user.department,
            'role': current_user.role
        }
        
        # RNCs que o usuário deveria ver
        if current_user.role == 'admin':
            # Admin vê todas
            cur.execute("SELECT id, rnc_number, title, department, user_id FROM rncs ORDER BY created_at DESC LIMIT 10")
        else:
            # Usuário normal vê suas próprias + do seu departamento
            cur.execute("""
                SELECT id, rnc_number, title, department, user_id 
                FROM rncs 
                WHERE user_id = ? OR department = ?
                ORDER BY created_at DESC LIMIT 10
            """, (current_user.id, current_user.department))
        
        rncs = []
        for row in cur.fetchall():
            rncs.append({
                'id': row[0],
                'rnc_number': row[1],
                'title': row[2],
                'department': row[3],
                'user_id': row[4]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'user_info': user_info,
            'rncs_visible': rncs,
            'total_visible': len(rncs)
        })
        
    except Exception as e:
        logger.error(f"Erro no debug de grupos: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/charts/data')
def get_charts_data():
    try:
        period = request.args.get('period', '30')
        
        # Conectar ao banco
        conn = sqlite3.connect('ippel_system.db')
        cursor = conn.cursor()
        
        # Dados para gráfico de status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM rnc_reports 
            WHERE created_at >= date('now', '-{} days')
            GROUP BY status
        """.format(period))
        status_data = cursor.fetchall()
        
        # Dados para gráfico de prioridade
        cursor.execute("""
            SELECT priority, COUNT(*) as count 
            FROM rnc_reports 
            WHERE created_at >= date('now', '-{} days')
            GROUP BY priority
        """.format(period))
        priority_data = cursor.fetchall()
        
        # Dados para gráfico mensal
        cursor.execute("""
            SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
            FROM rnc_reports 
            WHERE created_at >= date('now', '-{} days')
            GROUP BY month
            ORDER BY month
        """.format(period))
        monthly_data = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'status': [{'label': row[0], 'count': row[1]} for row in status_data],
                'priority': [{'label': row[0], 'count': row[1]} for row in priority_data],
                'monthly': [{'month': row[0], 'count': row[1]} for row in monthly_data]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/indicadores-dashboard')
@app.route('/indicadores')
@login_required
def indicadores_dashboard():
    """Nova página de indicadores baseada na imagem fornecida"""
    return render_template('indicadores_dashboard.html')

@app.route('/api/indicadores-detalhados')
def get_indicadores_detalhados():
    """API para dados detalhados dos indicadores com formato específico"""
    try:
        conn = sqlite3.connect('ippel_system.db')
        cursor = conn.cursor()
        
        # Verificar se existe a tabela
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rncs'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            conn.close()
            return jsonify(get_fallback_indicadores_data())
        
        # Obter dados do ano atual
        current_year = datetime.now().year
        
        # Total de RNCs
        cursor.execute("SELECT COUNT(*) FROM rncs WHERE strftime('%Y', created_at) = ?", (str(current_year),))
        total_rncs_year = cursor.fetchone()[0]
        
        # Total geral
        cursor.execute("SELECT COUNT(*) FROM rncs")
        total_rncs_all = cursor.fetchone()[0]
        
        # Dados por usuário (simulando departamentos)
        cursor.execute("""
            SELECT u.name, COUNT(r.id) as count 
            FROM rncs r 
            LEFT JOIN users u ON r.user_id = u.id 
            WHERE r.created_at >= date('now', '-12 months')
            GROUP BY u.name, r.user_id
            ORDER BY count DESC
            LIMIT 4
        """)
        user_data = cursor.fetchall()
        
        # Se não há dados de usuários, usar dados por status
        if not user_data:
            user_data = [
                ('ÁREA CORPORATIVO', max(1, total_rncs_year // 4)),
                ('CONTROLE', max(1, total_rncs_year // 3)),
                ('ALAN', max(1, total_rncs_year // 5)),
                ('MARCELO', max(1, total_rncs_year // 5))
            ]
        
        # Dados mensais do ano atual
        cursor.execute("""
            SELECT 
                strftime('%m', created_at) as month,
                COUNT(*) as count
            FROM rncs 
            WHERE strftime('%Y', created_at) = ?
            GROUP BY strftime('%m', created_at)
            ORDER BY month
        """, (str(current_year),))
        monthly_raw = cursor.fetchall()
        
        # Status das RNCs para calcular eficiência
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN status = 'finalizado' THEN 'finalizado'
                    ELSE 'ativo'
                END as status_group,
                COUNT(*) as count
            FROM rncs 
            WHERE strftime('%Y', created_at) = ?
            GROUP BY status_group
        """, (str(current_year),))
        status_data = cursor.fetchall()
        
        conn.close()
        
        # Processar dados mensais
        month_names = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 
                      'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        
        monthly_data = []
        monthly_counts = {row[0]: row[1] for row in monthly_raw}
        acumulado = 0
        
        for i, month_name in enumerate(month_names):
            month_num = f"{i+1:02d}"
            realizado = monthly_counts.get(month_num, 0)
            acumulado += realizado
            
            monthly_data.append({
                'month': month_name,
                'meta': 15,  # Meta padrão, pode ser configurável
                'realizado': realizado,
                'acumulado': acumulado
            })
        
        # Calcular totais
        total_realizado = sum(d['realizado'] for d in monthly_data)
        total_meta = len(monthly_data) * 15  # 15 por mês
        variacao = total_meta - total_realizado
        
        # Processar departamentos/usuários
        departments = []
        for name, count in user_data:
            if name:  # Filtrar nomes nulos
                departments.append({
                    'name': str(name)[:20],  # Limitar tamanho do nome
                    'realizado': count,
                    'meta': max(count + 5, 10)  # Meta ligeiramente maior que realizado
                })
        
        # Se não há departamentos, usar dados de fallback
        if not departments:
            departments = [
                {'name': 'ÁREA CORPORATIVO', 'realizado': max(1, total_realizado // 4), 'meta': 12},
                {'name': 'CONTROLE', 'realizado': max(1, total_realizado // 3), 'meta': 15},
                {'name': 'ALAN', 'realizado': max(1, total_realizado // 5), 'meta': 8},
                {'name': 'MARCELO', 'realizado': max(1, total_realizado // 5), 'meta': 10}
            ]
        
        # Calcular eficiência baseada em finalizados
        finalizados = sum(count for status, count in status_data if status == 'finalizado')
        efficiency = (finalizados / total_rncs_year * 100) if total_rncs_year > 0 else 0
        
        result = {
            'totals': {
                'meta': float(total_meta),
                'realizado': float(total_realizado),
                'variacao': float(variacao),
                'acumulado': total_realizado,
                'efficiency': round(efficiency, 1),
                'total_all_time': total_rncs_all
            },
            'departments': departments,
            'monthlyData': monthly_data,
            'stats': {
                'finalizados': finalizados,
                'ativos': total_rncs_year - finalizados,
                'efficiency_rate': round(efficiency, 1)
            }
        }
        
        print(f"✅ Indicadores detalhados carregados: {total_rncs_year} RNCs no ano, {total_rncs_all} total")
        return jsonify(result)
        
    except Exception as e:
        print(f"Erro ao carregar indicadores detalhados: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(get_fallback_indicadores_data())

def get_fallback_indicadores_data():
    """Dados de fallback baseados na imagem fornecida"""
    return {
        'totals': {
            'meta': 15.00,
            'realizado': 6.33,
            'variacao': 8.67,
            'acumulado': 15
        },
        'departments': [
            {'name': 'ÁREA CORPORATIVO', 'realizado': 5, 'meta': 12},
            {'name': 'CONTROLE', 'realizado': 13, 'meta': 15},
            {'name': 'ALAN', 'realizado': 6, 'meta': 8},
            {'name': 'MARCELO', 'realizado': 6, 'meta': 10}
        ],
        'monthlyData': [
            {'month': 'JAN', 'meta': 15, 'realizado': 0, 'acumulado': 0},
            {'month': 'FEV', 'meta': 15, 'realizado': 0, 'acumulado': 0},
            {'month': 'MAR', 'meta': 15, 'realizado': 0, 'acumulado': 0},
            {'month': 'ABR', 'meta': 15, 'realizado': 0, 'acumulado': 0},
            {'month': 'MAI', 'meta': 15, 'realizado': 0, 'acumulado': 0},
            {'month': 'JUN', 'meta': 15, 'realizado': 5, 'acumulado': 5},
            {'month': 'JUL', 'meta': 15, 'realizado': 12, 'acumulado': 17},
            {'month': 'AGO', 'meta': 15, 'realizado': 13, 'acumulado': 30},
            {'month': 'SET', 'meta': 15, 'realizado': 0, 'acumulado': 30},
            {'month': 'OUT', 'meta': 15, 'realizado': 0, 'acumulado': 30},
            {'month': 'NOV', 'meta': 15, 'realizado': 0, 'acumulado': 30},
            {'month': 'DEZ', 'meta': 15, 'realizado': 0, 'acumulado': 30}
        ]
    }

@app.route('/api/indicadores')
def get_indicadores_data():
    """Endpoint para dados dos indicadores - versão simplificada para debug"""
    try:
        # Dados de teste fixos para debug
        test_data = {
            'kpis': {
                'total_rncs': 150,
                'total_metas': 200,
                'active_departments': 3,
                'overall_efficiency': 75.0,
                'avg_rncs_per_dept': 50.0
            },
            'departments': [
                {'department': 'PRODUÇÃO', 'meta': 80, 'realizado': 60, 'efficiency': 75.0},
                {'department': 'ENGENHARIA', 'meta': 70, 'realizado': 55, 'efficiency': 78.6},
                {'department': 'QUALIDADE', 'meta': 50, 'realizado': 35, 'efficiency': 70.0}
            ],
            'monthly_trends': [
                {'month': 'JAN', 'total': 15, 'date': '2024-01-01'},
                {'month': 'FEV', 'total': 18, 'date': '2024-02-01'},
                {'month': 'MAR', 'total': 12, 'date': '2024-03-01'},
                {'month': 'ABR', 'total': 20, 'date': '2024-04-01'},
                {'month': 'MAI', 'total': 16, 'date': '2024-05-01'},
                {'month': 'JUN', 'total': 14, 'date': '2024-06-01'},
                {'month': 'JUL', 'total': 19, 'date': '2024-07-01'},
                {'month': 'AGO', 'total': 22, 'date': '2024-08-01'}
            ]
        }
        
        print("📊 Retornando dados de teste para indicadores")
        return jsonify(test_data)
        
    except Exception as e:
        print(f"❌ Erro no endpoint de indicadores: {e}")
        # Fallback simples
        fallback_data = {
            'kpis': {
                'total_rncs': 100,
                'total_metas': 120,
                'active_departments': 2,
                'overall_efficiency': 60.0,
                'avg_rncs_per_dept': 50.0
            },
            'departments': [
                {'department': 'TESTE1', 'meta': 60, 'realizado': 40, 'efficiency': 66.7},
                {'department': 'TESTE2', 'meta': 60, 'realizado': 50, 'efficiency': 83.3}
            ],
            'monthly_trends': [
                {'month': 'JAN', 'total': 10, 'date': '2024-01-01'},
                {'month': 'FEV', 'total': 15, 'date': '2024-02-01'}
            ]
        }
        
        return jsonify(fallback_data)
            
    except Exception as e:
        print(f"Erro ao carregar indicadores: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ===== EVENTOS DO SOCKET.IO =====

@socketio.on('connect')
def handle_connect():
    """Evento de conexão do Socket.IO"""
    print(f'✅ Cliente conectado: {request.sid}')
    emit('connected', {'message': 'Conectado com sucesso'})

@socketio.on('disconnect')
def handle_disconnect():
    """Evento de desconexão do Socket.IO"""
    print(f'❌ Cliente desconectado: {request.sid}')

@socketio.on('join_room')
def handle_join_room(data):
    """Entrar em uma sala do chat"""
    room = data.get('room')
    if room:
        join_room(room)
        print(f'🔌 Cliente {request.sid} entrou na sala: {room}')
        emit('room_joined', {'room': room, 'message': 'Entrou na sala com sucesso'})

@socketio.on('leave_room')
def handle_leave_room(data):
    """Sair de uma sala do chat"""
    room = data.get('room')
    if room:
        leave_room(room)
        print(f'🚪 Cliente {request.sid} saiu da sala: {room}')

@socketio.on('send_message')
def handle_send_message(data):
    """Enviar mensagem no chat"""
    try:
        rnc_id = data.get('rnc_id')
        message_text = data.get('message', '').strip()
        chat_type = data.get('chat_type', 'rnc')
        
        if not message_text:
            emit('error', {'message': 'Mensagem não pode estar vazia'})
            return
        
        # Verificar se o usuário está logado (simplificado para Socket.IO)
        # Em produção, você deveria verificar a sessão do usuário
        
        # Salvar mensagem no banco
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_messages (rnc_id, user_id, message, message_type, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (rnc_id, 1, message_text, 'text'))  # Usar ID 1 temporariamente
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Preparar dados da mensagem
        message_data = {
            'id': message_id,
            'rnc_id': rnc_id,
            'user_id': 1,  # Temporário
            'message': message_text,
            'message_type': 'text',
            'created_at': datetime.now().isoformat(),
            'user_name': 'Usuário',  # Temporário
            'department': ''
        }
        
        # Enviar mensagem para todos na sala
        room = f'rnc_{rnc_id}'
        emit('new_message', message_data, room=room)
        emit('message_sent', {'success': True, 'message': message_data})
        
        print(f'📨 Mensagem enviada na sala {room}: {message_text}')
        
    except Exception as e:
        print(f'❌ Erro ao enviar mensagem: {e}')
        emit('error', {'message': 'Erro interno do servidor'})

# ===== ROTAS DO CHAT =====

@app.route('/rnc/<int:rnc_id>/chat')
@login_required
def rnc_chat(rnc_id):
    """Página do chat da RNC"""
    try:
        # Verificar se a RNC existe
        rnc_details = rnc_system.get_rnc_details(rnc_id)
        if not rnc_details:
            flash('RNC não encontrado', 'error')
            return redirect(url_for('dashboard'))
        
        # Verificar acesso
        is_owner = (rnc_details['main'][9] == current_user.id)
        is_admin = (current_user.role == 'admin')
        has_share = False
        if not (is_owner or is_admin):
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute('SELECT 1 FROM rnc_shares WHERE rnc_id = ? AND shared_with_user_id = ? LIMIT 1', (rnc_id, current_user.id))
                has_share = cur.fetchone() is not None
                conn.close()
            except Exception as ie:
                logger.error(f"Erro ao verificar compartilhamento da RNC {rnc_id}: {ie}")
        
        if not (is_owner or is_admin or has_share):
            flash('Acesso negado', 'error')
            return redirect(url_for('dashboard'))
        
        # Buscar mensagens do chat (com viewed_at para status WhatsApp)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cm.id, cm.user_id, u.name, cm.message, cm.message_type, cm.created_at, cm.viewed_at, u.department
            FROM chat_messages cm
            JOIN users u ON cm.user_id = u.id
            WHERE cm.rnc_id = ?
            ORDER BY cm.created_at ASC
        """, (rnc_id,))
        messages = cursor.fetchall()
        conn.close()
        
        # Preparar dados do usuário atual
        current_user_data = (current_user.id, current_user.name, current_user.email, current_user.department, current_user.role)
        
        return render_template('rnc_chat.html', 
                             rnc=rnc_details['main'], 
                             messages=messages, 
                             current_user=current_user_data)
        
    except Exception as e:
        logger.error(f"Erro ao carregar chat da RNC {rnc_id}: {e}")
        flash('Erro interno do sistema', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/chat/<int:rnc_id>/messages', methods=['POST'])
@login_required
def send_chat_message(rnc_id):
    """API para enviar mensagem no chat da RNC"""
    try:
        data = request.get_json()
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return jsonify({'success': False, 'message': 'Mensagem não pode estar vazia'}), 400
        
        # Verificar se a RNC existe e se o usuário tem acesso
        rnc_details = rnc_system.get_rnc_details(rnc_id)
        if not rnc_details:
            return jsonify({'success': False, 'message': 'RNC não encontrada'}), 404
        
        # Verificar acesso
        is_owner = (rnc_details['main'][9] == current_user.id)
        is_admin = (current_user.role == 'admin')
        has_share = False
        if not (is_owner or is_admin):
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute('SELECT 1 FROM rnc_shares WHERE rnc_id = ? AND shared_with_user_id = ? LIMIT 1', (rnc_id, current_user.id))
                has_share = cur.fetchone() is not None
                conn.close()
            except Exception as ie:
                logger.error(f"Erro ao verificar compartilhamento da RNC {rnc_id}: {ie}")
        
        if not (is_owner or is_admin or has_share):
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Salvar mensagem no banco
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_messages (rnc_id, user_id, message, message_type, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (rnc_id, current_user.id, message_text, 'text'))
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # 🔔 NOTIFICAÇÃO PERSISTENTE: Nova Resposta no Chat
        try:
            from services.persistent_notifications_service import PersistentNotificationService
            notification_service = PersistentNotificationService()
            
            change_details = {
                'action': 'chat_response',
                'user': current_user.username,
                'message': message_text[:100] + ('...' if len(message_text) > 100 else ''),
                'department': current_user.department,
                'message_id': message_id
            }
            notification_service.log_rnc_change(
                rnc_id=rnc_id,
                user_id=current_user.id,
                change_type='chat_response',
                change_details=change_details
            )
            logger.info(f"✅ Notificação persistente de resposta criada para RNC {rnc_id} por {current_user.username}")
        except Exception as e:
            logger.error(f"❌ Erro ao criar notificação de resposta para RNC {rnc_id}: {e}")
        
        # Preparar resposta
        message_data = {
            'id': message_id,
            'rnc_id': rnc_id,
            'user_id': current_user.id,
            'message': message_text,
            'message_type': 'text',
            'created_at': datetime.now().isoformat(),
            'user_name': current_user.name,
            'department': current_user.department
        }
        
        return jsonify({'success': True, 'message': message_data})
        
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem no chat da RNC {rnc_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do sistema'}), 500

@app.route('/api/chat/<int:rnc_id>/messages/<int:message_id>', methods=['DELETE'])
@login_required
def delete_chat_message(rnc_id, message_id):
    """API para deletar mensagem do chat da RNC"""
    try:
        # Verificar se a mensagem existe e se o usuário pode deletá-la
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id FROM chat_messages 
            WHERE id = ? AND rnc_id = ?
        """, (message_id, rnc_id))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'success': False, 'message': 'Mensagem não encontrada'}), 404
        
        message_user_id = result[0]
        
        # Verificar se o usuário pode deletar (própria mensagem ou admin)
        if message_user_id != current_user.id and current_user.role != 'admin':
            conn.close()
            return jsonify({'success': False, 'message': 'Acesso negado'}), 403
        
        # Deletar mensagem
        cursor.execute("DELETE FROM chat_messages WHERE id = ?", (message_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Mensagem deletada com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao deletar mensagem {message_id} do chat da RNC {rnc_id}: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do sistema'}), 500

@app.route('/form_ata')
@login_required
def form_ata():
    """Página de criação de ata de reunião"""
    return render_template('form_ata.html')

@app.route('/api/ata/create', methods=['POST'])
@login_required
def create_ata():
    """API para criar nova ata de reunião"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS atas_reuniao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT NOT NULL,
                data_reuniao TEXT NOT NULL,
                local TEXT,
                assunto TEXT NOT NULL,
                participantes TEXT,
                conteudo TEXT NOT NULL,
                decisoes TEXT,
                responsaveis TEXT,
                prazo TEXT,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'ativa',
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # Inserir ata
        cursor.execute("""
            INSERT INTO atas_reuniao 
            (numero, data_reuniao, local, assunto, participantes, conteudo, 
             decisoes, responsaveis, prazo, created_by, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ativa')
        """, (
            data.get('numero'),
            data.get('data_reuniao'),
            data.get('local'),
            data.get('assunto'),
            data.get('participantes'),
            data.get('conteudo'),
            data.get('decisoes'),
            data.get('responsaveis'),
            data.get('prazo'),
            current_user.id
        ))
        
        ata_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Ata criada com sucesso',
            'ata_id': ata_id
        })
        
    except Exception as e:
        logger.error(f"Erro ao criar ata: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/atas/list')
@login_required
def list_atas():
    """API para listar atas de reunião"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.id, a.numero, a.data_reuniao, a.assunto, a.status,
                   a.created_at, u.name as criador
            FROM atas_reuniao a
            LEFT JOIN users u ON a.created_by = u.id
            ORDER BY a.data_reuniao DESC, a.created_at DESC
        """)
        
        atas = []
        for row in cursor.fetchall():
            atas.append({
                'id': row[0],
                'numero': row[1],
                'data_reuniao': row[2],
                'assunto': row[3],
                'status': row[4],
                'created_at': row[5],
                'criador': row[6]
            })
        
        conn.close()
        return jsonify({'success': True, 'atas': atas})
        
    except Exception as e:
        logger.error(f"Erro ao listar atas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    # Inicializar banco de dados
    init_database()
    
    # Executar migrações necessárias
    migrate_users_table()
    
    # Registrar rotas de notificações persistentes
    if notification_service:
        try:
            register_persistent_notifications_routes(app)
            logger.info("✅ Rotas de notificações persistentes registradas")
        except Exception as e:
            logger.error(f"❌ Erro ao registrar rotas de notificações: {e}")
    
    # Iniciar backup automático do banco (imediato e a cada 8 minutos)
    try:
        start_backup_scheduler(interval_seconds=480)
    except Exception as e:
        print(f"Falha ao iniciar backup automático: {e}")
    
    # Obter IP local
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"
    
    # 🔐 Configuração SSL/HTTPS
    import os
    ssl_cert_path = os.path.join(os.path.dirname(__file__), 'ssl_certs', 'cert.pem')
    ssl_key_path = os.path.join(os.path.dirname(__file__), 'ssl_certs', 'key.pem')
    
    use_https = os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path)
    protocol = "https" if use_https else "http"
    
    print("🚀 Sistema IPPEL Admin iniciado!")
    print("=" * 50)
    if use_https:
        print("🔐 HTTPS ATIVADO - Conexão Segura!")
        print(f"📊 Painel Admin: https://{local_ip}:5000")
        print(f"📋 Formulário: https://{local_ip}:5001")
        print("\n⚠️  AVISO: Certificado auto-assinado")
        print("   Aceite o aviso de segurança no navegador")
    else:
        print("⚠️  HTTP (não seguro) - Gere certificados SSL")
        print(f"📊 Painel Admin: http://{local_ip}:5000")
        print(f"📋 Formulário: http://{local_ip}:5001")
        print("\n💡 Para ativar HTTPS:")
        print("   Execute: python gerar_certificado_ssl.py")
    print("=" * 50)
    print("💡 Use o start_admin.bat para iniciar este servidor")
    print("💡 Use o start_form.bat para iniciar o formulário")
    print("=" * 50)
    
    # Iniciar com ou sem SSL
    if use_https:
        socketio.run(app, debug=False, host='0.0.0.0', port=5000,
                    certfile=ssl_cert_path, keyfile=ssl_key_path)
    else:
        socketio.run(app, debug=False, host='0.0.0.0', port=5000)