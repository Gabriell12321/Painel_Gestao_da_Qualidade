# 📚 Documentação Completa - Sistema IPPEL RNC

**Versão:** 1.0.0  
**Data:** Fevereiro de 2026  
**Status:** ✅ Produção  

---

## 📋 Sumário

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Instalação e Configuração](#instalação-e-configuração)
4. [Banco de Dados](#banco-de-dados)
5. [APIs e Endpoints](#apis-e-endpoints)
6. [Sistema de Relatórios](#sistema-de-relatórios)
7. [Segurança](#segurança)
8. [Permissões](#permissões)
9. [Notificações](#notificações)
10. [Microserviços](#microserviços)
11. [Frontend](#frontend)
12. [Testes](#testes)
13. [Troubleshooting](#troubleshooting)
14. [Roadmap](#roadmap)

---

## 🎯 Visão Geral

O **Sistema IPPEL RNC** é uma plataforma enterprise para gestão completa de **Relatórios de Não Conformidade (RNC)**, construída com arquitetura híbrida (monolito modular + microserviços opcionais).

### Principais Funcionalidades

- ✅ Gestão completa de RNCs (criação, edição, aprovação, compartilhamento)
- ✅ Controle de Qualidade (inspeção, engenharia, assinaturas digitais)
- ✅ Sistema de Disposições (usar, retrabalhar, rejeitar, sucata, devolver)
- ✅ Relatórios Avançados (por período, operador, setor, cliente)
- ✅ Analytics em Tempo Real (dashboards interativos com Chart.js)
- ✅ Comunicação Integrada (chat geral, por RNC, mensagens privadas)
- ✅ Gestão de Permissões (controle granular por campo - 46 campos)

### Métricas do Sistema

| Métrica | Valor |
|---------|-------|
| RNCs ativas | 3.694+ |
| Histórico total | 21.341+ registros |
| Tamanho DB | ~2.5MB (otimizado) |
| Pool conexões | 150 conexões |
| Performance | 1.000+ registros/min |
| Tempo resposta | < 200ms típico |

---

## 🏗️ Arquitetura do Sistema

### Backend Principal

```
┌─────────────────────────────────────────────────────────┐
│                    Flask Application                     │
│                   (server_form.py)                       │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  Routes  │ │ Services │ │  Utils   │ │  Config  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Blueprints (routes/)                 │   │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌──────┐ ┌─────────┐   │   │
│  │  │ api │ │auth │ │ rnc │ │admin │ │ reports │   │   │
│  │  └─────┘ └─────┘ └─────┘ └──────┘ └─────────┘   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Estrutura de Diretórios

```
Z:\rnc pdc\
├── server_form.py              # Servidor principal (10.9k linhas)
├── main_system.py              # Sistema alternativo (2.8k linhas)
├── dashboard_improved.html     # Dashboard (23.4k linhas)
├── ippel_system.db             # Banco de dados SQLite
│
├── app/                        # App modular (em migração)
│   ├── config.py
│   └── routes/
│
├── routes/                     # Blueprints Flask
│   ├── api.py                  # APIs gerais
│   ├── auth.py                 # Autenticação
│   ├── rnc.py                  # CRUD de RNCs
│   ├── admin.py                # Administração
│   ├── report.py               # Relatórios
│   └── print_reports.py        # Impressão
│
├── services/                   # Serviços Python
│   ├── db.py                   # Pool de conexões
│   ├── cache.py                # Cache system
│   ├── permissions.py          # Sistema de permissões
│   ├── users.py                # Gestão de usuários
│   ├── rnc.py                  # Lógica de RNCs
│   ├── jwt_auth.py             # JWT tokens
│   ├── lockout.py              # Progressive lockout
│   ├── security_log.py         # Security logging
│   ├── notifications_api.py    # Notificações REST
│   ├── notification_socketio.py # WebSocket notifications
│   ├── persistent_notifications_service.py
│   ├── validation.py           # Validação de dados
│   ├── pagination.py           # Paginação
│   ├── pdf_generator.py        # Geração de PDFs
│   ├── image_utils.py          # Processamento de imagens
│   └── database_optimizer.py   # Otimização DB
│
├── static/                     # Assets frontend
│   ├── css/
│   ├── js/
│   ├── uploads/
│   └── avatars/
│
├── templates/                  # Templates HTML
│   ├── dashboard_improved.html
│   ├── new_rnc.html
│   ├── view_rnc.html
│   ├── login.html
│   └── reports/
│
├── src/                        # Frontend React/TS
│   ├── components/
│   ├── hooks/
│   └── utils/
│
├── tests/                      # Testes (150+ arquivos)
├── docs/                       # Documentação
├── migrations/                 # Migrações de banco
├── logs/                       # Logs do sistema
└── backups/                    # Backups do banco
```

### Microserviços Polyglot

| Serviço | Porta | Linguagem | Finalidade |
|---------|-------|-----------|------------|
| Rust Images | 8081 | Rust (Actix) | Processamento de imagens |
| Julia Analytics | 8082 | Julia | Analytics estatístico |
| Go Reports | 8083 | Go (Gin) | Geração de PDFs |
| Kotlin Utils | 8084 | Kotlin/JVM | QR codes (ZXing) |
| Swift Tools | 8085 | Swift | Hash/criptografia |
| Scala Tools | 8086 | Scala | Base64 encode/decode |
| Nim Tools | 8087 | Nim | UUID/token generation |
| V Tools | 8088 | V | Slugify |
| Haskell Tools | 8089 | Haskell | Levenshtein distance |
| Zig Tools | 8090 | Zig | XXH3 hash |
| Crystal Tools | 8091 | Crystal | SHA256 |
| Deno Tools | 8092 | Deno/TS | URL encode/decode |

**Estratégia de Fallback:** Todos os microserviços possuem fallback silencioso - o sistema funciona 100% mesmo sem nenhum serviço auxiliar.

---

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.9+
- Node.js 16+ (opcional, para frontend React)
- SQLite 3.35+
- (Opcional) Redis para cache distribuído

### Instalação do Backend

```bash
# 1. Clonar repositório
cd Z:\rnc pdc

# 2. Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install flask flask-socketio flask-compress flask-talisman
pip install PyJWT bleach Pillow reportlab
pip install python-dateutil werkzeug

# 4. Configurar variáveis de ambiente
# Copie .env.example para .env (se existir)
cp .env.example .env

# 5. Inicializar banco de dados
python -c "from server_form import init_database; init_database()"

# 6. Iniciar servidor
python server_form.py
```

### Variáveis de Ambiente

```bash
# Flask
FLASK_ENV=production
FLASK_SECRET_KEY=sua-chave-secreta-aqui

# JWT
JWT_SECRET=sua-chave-jwt-secreta
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=604800

# Banco de Dados
IPPEL_BACKUP_DIR=G:\My Drive\BACKUP BANCO DE DADOS IPPEL

# Rate Limiting
RATE_LIMIT_DEFAULTS=200 per minute

# CSRF (opcional)
CSRF_ENFORCE=false

# Microserviços (opcionais)
RUST_IMAGES_URL=http://localhost:8081
JULIA_ANALYTICS_URL=http://localhost:8082
GO_REPORTS_URL=http://localhost:8083
KOTLIN_UTILS_URL=http://localhost:8084
```

### Inicialização

```bash
# Iniciar servidor principal
python server_form.py

# Ou usar script batch (Windows)
iniciar_todos_definitivo.bat
```

O servidor estará disponível em: `http://localhost:5001`

---

## 🗄️ Banco de Dados

### Tabelas Principais

#### `users` - Usuários do Sistema
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    department TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    permissions TEXT DEFAULT '[]',
    group_id INTEGER,
    avatar_key TEXT,
    avatar_prefs TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (group_id) REFERENCES groups (id)
);
```

#### `rncs` - Relatórios de Não Conformidade
```sql
CREATE TABLE rncs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rnc_number TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    equipment TEXT,
    client TEXT,
    priority TEXT DEFAULT 'Média',
    status TEXT DEFAULT 'Pendente',
    user_id INTEGER,
    assigned_user_id INTEGER,
    area_responsavel TEXT,
    setor TEXT,
    responsavel TEXT,
    price REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finalized_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT 0,
    -- Disposições
    disposition_usar BOOLEAN DEFAULT 0,
    disposition_retrabalhar BOOLEAN DEFAULT 0,
    disposition_rejeitar BOOLEAN DEFAULT 0,
    disposition_sucata BOOLEAN DEFAULT 0,
    -- Assinaturas
    signature_inspection_name TEXT,
    signature_inspection_date TEXT,
    signature_engineering_name TEXT,
    signature_engineering_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (assigned_user_id) REFERENCES users (id)
);
```

#### `groups` - Grupos/Departamentos
```sql
CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    manager_user_id INTEGER,
    sub_manager_user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `group_permissions` - Permissões por Grupo
```sql
CREATE TABLE group_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    permission_name TEXT NOT NULL,
    permission_value BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, permission_name)
);
```

#### `rnc_shares` - Compartilhamento de RNCs
```sql
CREATE TABLE rnc_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rnc_id INTEGER NOT NULL,
    shared_by_user_id INTEGER NOT NULL,
    shared_with_user_id INTEGER NOT NULL,
    permission_level TEXT DEFAULT 'view',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(rnc_id, shared_with_user_id)
);
```

#### `notifications` - Notificações
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    priority TEXT DEFAULT 'normal',
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    data TEXT,
    from_user_id INTEGER,
    to_user_id INTEGER NOT NULL,
    rnc_id INTEGER,
    is_read BOOLEAN DEFAULT 0,
    is_dismissed BOOLEAN DEFAULT 0,
    read_at TIMESTAMP,
    dismissed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
```

#### `chat_messages` - Mensagens do Chat
```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rnc_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    message_type TEXT DEFAULT 'text',
    file_data BLOB,
    file_name TEXT,
    file_path TEXT,
    viewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Índices de Performance

```sql
-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_users_group_id ON users(group_id);
CREATE INDEX idx_users_active ON users(is_active);

-- RNCs
CREATE INDEX idx_rncs_number ON rncs(rnc_number);
CREATE INDEX idx_rncs_user_id ON rncs(user_id);
CREATE INDEX idx_rncs_assigned_user_id ON rncs(assigned_user_id);
CREATE INDEX idx_rncs_status ON rncs(status);
CREATE INDEX idx_rncs_priority ON rncs(priority);
CREATE INDEX idx_rncs_is_deleted ON rncs(is_deleted);
CREATE INDEX idx_rncs_created_at ON rncs(created_at);
CREATE INDEX idx_rncs_finalized_at ON rncs(finalized_at);

-- Compostos
CREATE INDEX idx_rncs_status_deleted ON rncs(status, is_deleted);
CREATE INDEX idx_rncs_user_status ON rncs(user_id, status, is_deleted);
CREATE INDEX idx_rncs_dept_status ON rncs(department, status, is_deleted);
```

---

## 📡 APIs e Endpoints

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/login` | Login de usuário |
| GET | `/api/logout` | Logout de usuário |
| POST | `/api/refresh` | Refresh de token JWT |
| GET | `/api/csrf-token` | Obter token CSRF |

### RNCs

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/rncs/list` | Listar RNCs (paginado) |
| GET | `/api/rncs/{id}` | Obter RNC específica |
| POST | `/api/rncs/create` | Criar nova RNC |
| PUT | `/api/rncs/{id}/edit` | Editar RNC |
| DELETE | `/api/rncs/{id}/delete` | Deletar RNC (soft) |
| POST | `/api/rncs/{id}/share` | Compartilhar RNC |
| GET | `/api/rnc/next-number` | Próximo número de RNC |

### R.Os (Relatórios de Ocorrência)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/ro/list` | Listar R.Os |
| GET | `/api/ro/{id}` | Obter R.O específica |
| POST | `/api/ro/create` | Criar nova R.O |
| PUT | `/api/ro/{id}/edit` | Editar R.O |
| DELETE | `/api/ro/{id}/delete` | Deletar R.O |
| GET | `/api/ro/next-number` | Próximo número de R.O |

### Garantias

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/garantias/list` | Listar garantias |
| GET | `/api/garantias/{id}` | Obter garantia |
| POST | `/api/garantias/create` | Criar garantia |
| DELETE | `/api/garantias/{id}/delete` | Deletar garantia |

### Administração

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/admin/users` | Listar usuários |
| POST | `/api/admin/users/create` | Criar usuário |
| PUT | `/api/admin/users/{id}/update` | Atualizar usuário |
| DELETE | `/api/admin/users/{id}/delete` | Deletar usuário |
| GET | `/api/admin/groups` | Listar grupos |
| POST | `/api/admin/groups/create` | Criar grupo |
| GET | `/api/admin/field-locks` | Listar field locks |
| PUT | `/api/admin/field-locks/update` | Atualizar field locks |

### Relatórios

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/reports/menu` | Menu de relatórios |
| GET | `/reports/date_selection` | Seleção de datas |
| GET | `/reports/generate` | Gerar relatório |
| GET | `/report/print_rnc` | Imprimir RNC |

### Notificações

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/notifications/unread` | Notificações não lidas |
| POST | `/api/notifications/{id}/read` | Marcar como lida |
| POST | `/api/notifications/{id}/dismiss` | Dispensar notificação |
| GET | `/api/persistent-notifications/pending` | Notificações pendentes |

### Utilitários

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/sectors` | Listar setores |
| GET | `/api/users` | Listar usuários |
| GET | `/api/dashboard/performance` | Performance do dashboard |
| GET | `/dashboard/api/kpis` | KPIs do dashboard |

---

## 📄 Sistema de Relatórios

### Menu Principal

**URL:** `/reports/menu`

O sistema possui **5 tipos de relatórios** principais:

```
┌─────────────────────────────────────────┐
│         📊 RELATÓRIOS IPPEL             │
├─────────────────────────────────────────┤
│  [OK] RNCs Finalizados                  │
│  [++] Total Detalhado                   │
│  [@]  Por Operador                      │
│  [#]  Por Setor                         │
│  []   Pauta Reunião                     │
└─────────────────────────────────────────┘
```

### Fluxo de Geração

```
1. /reports/menu
   → Usuário escolhe tipo de relatório

2. /reports/date_selection?type={type}
   → Usuário seleciona período (data inicial/final)

3. /reports/generate?start_date={}&end_date={}&type={type}
   → Sistema gera relatório formatado para impressão
```

### Tipos de Relatórios

#### 1. RNCs Finalizados (`finalized`)
- **Foco:** Apenas RNCs com status "Finalizado"
- **Template:** `finalized_rncs_report.html`
- **Estatísticas:**
  - Total de finalizados
  - Valor total (R$)
  - Quantidade por departamento
  - Valor médio por departamento

#### 2. Total Detalhado (`total_detailed`)
- **Foco:** Todas as RNCs (pendentes + finalizadas)
- **Template:** `total_detailed_report.html`
- **Filtros:**
  - Por setor (todos ou específico)
  - Por valor mínimo/máximo
- **Estatísticas:**
  - Total de RNCs
  - Valor total
  - Por status
  - Por departamento

#### 3. Por Operador (`by_operator`)
- **Foco:** Performance individual por funcionário
- **Template:** `by_operator_report.html`
- **Agrupamento:** Departamento → Funcionário → RNCs
- **Filtros:** Status (finalizados, pendentes, ambos)

#### 4. Por Setor (`by_sector`)
- **Foco:** Análise departamental
- **Template:** `by_sector_report_simple.html`
- **Setores Consolidados:**
  - `Suprimentos` ← Terceiros, Compras
  - `Produção` ← Usinagem, Caldeiraria, Montagem, Pintura

#### 5. Pauta Reunião (`pauta_reuniao`)
- **Foco:** Resumo executivo para reuniões
- **Template:** `pauta_reuniao_report.html`
- **Tipos de Registro:** RNCs, R.Os, Garantias

### Filtros Jinja2 Customizados

```python
# Formatar número no estilo brasileiro: 1.234,56
{{ value|brl }}

# Formatar moeda: R$ 1.234,56
{{ value|brl_money }}

# Parse de string BRL para float
{{ value|parse_brl }}
```

---

## 🔐 Segurança

### Camadas de Proteção

#### 1. Autenticação e Autorização
- **Session-based + JWT** (migração em andamento)
- **2FA TOTP** (Google Authenticator, Authy)
- **Progressive Lockout** (5→15min, 10→1h, 15→24h)
- **Refresh Tokens** com rotação e revogação

#### 2. Proteção de Endpoints
- **CSRF Protection** (tokens automáticos)
- **Rate Limiting** (120-180 req/min por endpoint)
- **IP Allowlist** (para endpoints admin)
- **Permission Checks** (granular por ação)

#### 3. Validação de Dados
```python
class SecurityValidator:
    - Sanitização HTML (bleach)
    - Detecção XSS (padrões perigosos)
    - Detecção SQL Injection
    - Validação de upload de arquivos
    - Verificação de extensões perigosas
```

#### 4. Auditoria e Logging
- **Security Logs** (JSON estruturado)
- **Audit Trail** (todas as ações dos usuários)
- **Login Attempts** (rastreamento completo)
- **IP Blacklist** (bloqueio de IPs maliciosos)

### Progressive Lockout

```python
# services/lockout.py

def record_failure(user_id: int, ip: Optional[str] = None):
    """
    Registra falha de login e aplica lockout progressivo:
    - 5 falhas → 15 minutos de bloqueio
    - 10 falhas → 1 hora de bloqueio
    - 15 falhas → 24 horas de bloqueio
    """
```

### Security Headers

```python
# Content Security Policy
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'

# XSS Protection
X-XSS-Protection: 1; mode=block

# Clickjacking Protection
X-Frame-Options: SAMEORIGIN

# HTTPS Enforcement
Strict-Transport-Security: max-age=31536000
```

---

## 👥 Permissões

### Sistema de Permissões

O sistema utiliza um modelo híbrido de permissões baseado em **roles** e **departamentos**.

### Roles Disponíveis

| Role | Descrição |
|------|-----------|
| `admin` | Acesso total ao sistema |
| `user` | Usuário padrão |

### Permissões por Departamento

| Departamento | Permissões |
|--------------|------------|
| **Administração** | Todas as permissões |
| **TI** | Todas as permissões administrativas |
| **Qualidade** | view_all_rncs, view_finalized_rncs, view_charts, view_reports |
| **Produção** | view_own_rncs, edit_rncs |
| **Engenharia** | view_own_rncs, edit_rncs, view_engineering_rncs |

### Permissões Disponíveis

```python
# services/permissions.py

PERMISSIONS = {
    'view_all_rncs': 'Visualizar todas as RNCs',
    'view_finalized_rncs': 'Visualizar RNCs finalizadas',
    'view_charts': 'Visualizar gráficos e dashboards',
    'view_reports': 'Visualizar relatórios',
    'create_rnc': 'Criar novas RNCs',
    'edit_rncs': 'Editar RNCs',
    'delete_rncs': 'Excluir RNCs',
    'admin_access': 'Acesso administrativo',
    'manage_users': 'Gerenciar usuários',
    'view_levantamento_14_15': 'Visualizar levantamento 14/15',
    'can_print_reports': 'Imprimir relatórios',
}
```

### Verificação de Permissões

```python
from services.permissions import has_permission

# Verificar permissão
if has_permission(session['user_id'], 'create_rnc'):
    # Usuário tem permissão
    pass

# Decorator em rotas
@require_permission('admin_access')
def admin_route():
    pass
```

---

## 🔔 Notificações

### Tipos de Notificações

```python
class NotificationType(Enum):
    RNC_CREATED = "rnc_created"
    RNC_ASSIGNED = "rnc_assigned"
    RNC_UPDATED = "rnc_updated"
    RNC_COMMENTED = "rnc_commented"
    RNC_FINALIZED = "rnc_finalized"
    RNC_SHARED = "rnc_shared"
    SYSTEM_ALERT = "system_alert"
    APPROVAL_REQUEST = "approval_request"
```

### Notificações Persistentes

Sistema de notificações "chatas" que exigem resposta do usuário:

- Reexibição a cada 5 minutos
- Máximo de 10 tentativas
- Rastreamento de respostas
- Só desaparecem após resposta

### Socket.IO (Tempo Real)

```javascript
// Conectar ao namespace de notificações
const socket = io('/notifications');

// Ouvir notificações
socket.on('notifications_sync', (data) => {
    console.log('Notificações sincronizadas:', data.notifications);
});

// Marcar como lida
socket.emit('mark_notification_read', {
    notification_id: '123'
});

// Dispensar notificação
socket.emit('dismiss_notification', {
    notification_id: '123'
});
```

---

## 🔧 Microserviços

### Rust Images Service (Porta 8081)

```rust
// Processamento de imagens
POST /sanitize
GET /resize
GET /convert
```

### Julia Analytics Service (Porta 8082)

```julia
# Analytics estatístico
GET /api/analytics/summary
GET /api/analytics/trends
```

### Go Reports Service (Porta 8083)

```go
// Geração de PDFs
GET /reports/rnc/:id.pdf
```

### Kotlin Utils Service (Porta 8084)

```kotlin
// Geração de QR codes
GET /api/utils/qr.png?text={texto}
```

---

## 🎨 Frontend

### Dashboard Principal

**Template:** `dashboard_improved.html` (23.410 linhas)

**Features:**
- Gráficos Chart.js interativos
- Filtros por setor, período, prioridade
- Abas: Ativos, Finalizados, Gráficos, Setores
- Modos: RNC, R.O, Garantias, Atas
- Notificações em tempo real (Socket.IO)

### Estilos

```css
:root {
    --primary: #c0392b;
    --primary-dark: #962d22;
    --bg-dark: #263238;
    --text-primary: #263238;
    --success: #2E7D32;
    --warning: #F57F17;
    --info: #1565C0;
}
```

### Scripts Principais

```javascript
// Alternar entre RNC e R.O
window.switchMode = function(mode) {
    window.currentMode = mode;
    // Recarrega dados do modo selecionado
};

// Renderizar RNCs
window.renderRNCs = function(tab) {
    // Renderiza cards de RNC
};

// Socket.IO para notificações
socket.on('new_notification', (data) => {
    // Mostra notificação em tempo real
});
```

---

## 🧪 Testes

### Executar Testes

```bash
# Instalar pytest
pip install pytest pytest-cov

# Executar todos os testes
pytest tests/ -v

# Executar com coverage
pytest tests/ --cov=. --cov-report=html

# Executar testes específicos
pytest tests/test_api.py -v
pytest tests/test_auth.py -v
```

### Estrutura de Testes

```
tests/
├── test_api.py              # Testes de API
├── test_auth.py             # Testes de autenticação
├── test_rnc.py              # Testes de RNC
├── test_permissions.py      # Testes de permissões
├── test_reports.py          # Testes de relatórios
├── test_security.py         # Testes de segurança
└── debug_*.py               # Scripts de debug
```

---

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão com Banco de Dados

```python
# Verificar se o banco existe
import os
if not os.path.exists('ippel_system.db'):
    from server_form import init_database
    init_database()
```

#### 2. Database Locked

```python
# Aumentar timeout de conexão
conn = sqlite3.connect(DB_PATH, timeout=30)

# Habilitar WAL mode
conn.execute('PRAGMA journal_mode=WAL')
```

#### 3. Erro de Permissão

```python
# Verificar permissões do usuário
from services.permissions import has_permission

if not has_permission(user_id, 'admin_access'):
    raise PermissionError("Acesso negado")
```

#### 4. Microserviço Offline

Todos os microserviços possuem fallback. Se um serviço estiver offline, o sistema usa a implementação Python padrão.

### Logs

```bash
# Ver logs do sistema
tail -f logs/ippel_system.log

# Ver logs de segurança
tail -f logs/security.log

# Ver logs de erro
tail -f logs/error.log
```

---

## 📈 Roadmap

### Q1 2026

- [ ] Modularização do backend (refatorar `server_form.py`)
- [ ] Suite de testes automatizados (60% coverage)
- [ ] Documentação OpenAPI/Swagger

### Q2 2026

- [ ] Pipeline CI/CD (GitHub Actions)
- [ ] Dashboard de health de microserviços
- [ ] Cache Redis para dashboards

### Q3-Q4 2026

- [ ] PWA offline capabilities
- [ ] WebSocket real-time updates
- [ ] ML predictivo para analytics

---

## 📞 Suporte

### Contatos

- **Email:** suporte@ippel.com.br
- **Documentação:** `/docs`
- **Logs:** `/logs`

### Recursos Adicionais

- [API Endpoints](docs/API_ENDPOINTS.md)
- [Security Guide](docs/SECURITY.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Architecture](docs/ARCHITECTURE.md)

---

## 📄 Licença

**Proprietário:** IPPEL  
**Tipo:** Software Proprietário  
**Uso:** Interno  

---

*Documentação gerada em Fevereiro de 2026*
