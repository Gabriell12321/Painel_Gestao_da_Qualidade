# IPPEL RNC System - Sistema de Gestão de Relatórios de Não Conformidade

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3.35+-yellow.svg)
![License](https://img.shields.io/badge/License-MIT-red.svg)

## 📋 Visão Geral

O **IPPEL RNC System** é uma plataforma enterprise completa para gestão de **Relatórios de Não Conformidade (RNC)**, construída com arquitetura híbrida (monolito modular + microserviços opcionais).

### Principais Funcionalidades

- ✅ Gestão completa de RNCs (criação, edição, aprovação, compartilhamento)
- ✅ Controle de Qualidade (inspeção, engenharia, assinaturas digitais)
- ✅ Sistema de Disposições (usar, retrabalhar, rejeitar, sucata, devolver)
- ✅ Relatórios Avançados (por período, operador, setor, cliente)
- ✅ Analytics em Tempo Real (dashboards interativos com Chart.js)
- ✅ Comunicação Integrada (chat geral, por RNC, mensagens privadas)
- ✅ Gestão de Permissões (controle granular por campo - 46 campos)
<img width="1901" height="413" alt="image" src="https://github.com/user-attachments/assets/dfd9a659-3fd6-4f76-b688-a9cfc422d2d4" />

## 🏗️ Arquitetura do Sistema

### Backend Principal
- **Flask Application** (`server_form.py`) - Servidor principal com 10.941 linhas de código
- **SQLite Database** - Banco de dados leve e performático
- **Microserviços Polyglot** - 12 serviços em diferentes linguagens (opcional)

### Frontend
- **Templates HTML** - Interface web responsiva
- **React/TypeScript** - Novo frontend em desenvolvimento (`src/`)
- **CSS/JavaScript** - Estilos e interatividade

### Microserviços Disponíveis
| Linguagem | Porta | Finalidade |
|-----------|-------|------------|
| Rust | 8081 | Processamento de imagens |
| Julia | 8082 | Analytics estatístico |
| Go | 8083 | Geração de PDFs |
| Kotlin | 8084 | QR codes |
| Swift | 8085 | Hash/criptografia |
| Scala | 8086 | Base64 encode/decode |
| Nim | 8087 | UUID/token generation |
| V | 8088 | Slugify |
| Haskell | 8089 | Levenshtein distance |
| Zig | 8090 | XXH3 hash |
| Crystal | 8091 | SHA256 |
| Deno | 8092 | URL encode/decode |

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.9+
- Node.js 16+ (opcional, para frontend React)
- SQLite 3.35+
<img width="1919" height="740" alt="image" src="https://github.com/user-attachments/assets/f941f090-a9d5-49ed-b725-bc1eb274166a" />

### Instalação do Backend
<img width="244" height="773" alt="image" src="https://github.com/user-attachments/assets/17452698-df48-4e4f-9c38-9f99f4194598" />

```bash
# 1. Clonar repositório
git clone <repository-url>
cd rnc-pdc

# 2. Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install flask flask-socketio flask-compress flask-talisman
pip install PyJWT bleach Pillow reportlab
pip install python-dateutil werkzeug

# 4. Configurar variáveis de ambiente
# Copie config/.env.example para config/.env
cp config/.env.example config/.env

# 5. Inicializar banco de dados
python -c "from server_form import init_database; init_database()"

# 6. Iniciar servidor
python server_form.py
```

### Configuração de Variáveis de Ambiente

```bash
# Flask
FLASK_ENV=production
FLASK_SECRET_KEY=sua-chave-secreta-aqui

# JWT
JWT_SECRET=sua-chave-jwt-secreta
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=604800

# Banco de Dados
IPPEL_BACKUP_DIR=G:\Meu Drive\BACKUP BANCO DE DADOS IPPEL

# Rate Limiting
RATE_LIMIT_DEFAULTS=200 per minute

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

# Servidor estará disponível em: http://localhost:5001
```
<img width="1059" height="150" alt="image" src="https://github.com/user-attachments/assets/4de8d4f5-b30d-42ad-a82a-281aaff45975" />

## 🗄️ Estrutura do Banco de Dados

O sistema utiliza SQLite com as seguintes tabelas principais:

- `users` - Usuários do sistema
- `rncs` - Relatórios de Não Conformidade
- `groups` - Grupos/Departamentos
- `group_permissions` - Permissões por grupo
- `rnc_shares` - Compartilhamento de RNCs
- `notifications` - Sistema de notificações
- `chat_messages` - Mensagens do chat

## 🔐 Segurança

- Autenticação JWT com refresh tokens
- Progressive Lockout (5→15min, 10→1h, 15→24h)
- Rate Limiting (120-180 req/min)
- Validation de dados e sanitização HTML
- Security headers (CSP, XSS Protection)
- Audit trail completo

## 📊 Métricas do Sistema

| Métrica | Valor |
|---------|-------|
| RNCs ativas | 3.694+ |
| Histórico total | 21.341+ registros |
| Tamanho DB | ~2.5MB (otimizado) |
| Pool conexões | 150 conexões |
| Performance | 1.000+ registros/min |
| Tempo resposta | < 200ms típico |

## 📡 APIs e Endpoints

### Autenticação
- `POST /api/login` - Login de usuário
- `GET /api/logout` - Logout de usuário
- `POST /api/refresh` - Refresh de token JWT

### RNCs
- `GET /api/rncs/list` - Listar RNCs (paginado)
- `GET /api/rncs/{id}` - Obter RNC específica
- `POST /api/rncs/create` - Criar nova RNC
- `PUT /api/rncs/{id}/edit` - Editar RNC
- `DELETE /api/rncs/{id}/delete` - Deletar RNC

### Relatórios
- `GET /reports/menu` - Menu de relatórios
- `GET /reports/generate` - Gerar relatório
- `GET /report/print_rnc` - Imprimir RNC

## 🧪 Testes

```bash
# Instalar pytest
pip install pytest pytest-cov

# Executar testes
pytest tests/ -v

# Executar com coverage
pytest tests/ --cov=. --cov-report=html
```

## 📁 Estrutura de Diretórios

```
rnc-pdc/
├── server_form.py              # Servidor principal Flask
├── main_system.py              # Sistema alternativo
├── config/                     # Configurações
├── services/                    # Serviços Python
├── routes/                     # Blueprints Flask
├── templates/                  # Templates HTML
├── static/                     # Assets frontend
├── src/                        # Frontend React/TypeScript
├── tests/                      # Testes
├── docs/                       # Documentação
├── database/                   # Scripts de banco
├── data/                       # Dados (vazio no repositório)
├── logs/                       # Logs (vazio no repositório)
├── backups/                   # Backups (vazio no repositório)
└── microservicos/             # Microserviços polyglot
```

## 🔧 Desenvolvimento

### Scripts Úteis

```bash
# Iniciar servidor em modo desenvolvimento
python server_form.py

# Testar inicialização do banco
python -c "from server_form import init_database; init_database()"

# Verificar saúde dos microserviços
for port in 8081 8082 8083 8084 8085 8086 8087 8088 8089 8090 8091 8092; do
  curl -s http://localhost:$port/health
done
```

### Desenvolvimento de Microserviços

Cada microserviço pode ser desenvolvido independentemente:

```bash
# Rust
cd rust_images && cargo run --release

# Go
cd go_reports && go run main.go

# Kotlin
cd kotlin_utils && ./gradlew.bat run
```

## 📝 Documentação

- [Documentação Completa](DOCUMENTACAO_COMPLETA.md)
- [Estrutura do Projeto](ESTRUTURA_PROJETO.md)
- [Microserviços](MICROSERVICES.md)
- [Guia de APIs](docs/API_GUIDE.md)
- [Guia de Segurança](docs/SECURITY_GUIDE.md)
- [Guia de Deploy](docs/DEPLOYMENT_GUIDE.md)

## 🚀 Deploy

### Docker (Recomendado)

```bash
# Buildar imagem
docker build -t ippel-rnc-system .

# Rodar container
docker run -p 5001:5001 ippel-rnc-system
```

### Manual

1. Configure as variáveis de ambiente em `config/.env`
2. Inicialize o banco de dados
3. Inicie o servidor com `python server_form.py`
4. Configure proxy reverso (nginx) para produção

## 🔒 Considerações de Segurança

- **Nunca commit dados sensíveis** - O .gitignore está configurado para excluir bancos de dados, logs e dados
- **Use variáveis de ambiente** - Todas as configurações sensíveis devem estar em `.env`
- **Microserviços opcionais** - O sistema funciona 100% sem microserviços
- **Backup regular** - Configure backups automáticos do banco de dados

## 📞 Suporte

- **Email:** suporte@ippel.com.br
- **Documentação:** `/docs`
- **Issues:** [GitHub Issues](../../issues)

## 📄 Licença

**Proprietário:** IPPEL  
**Tipo:** Software Proprietário  
**Uso:** Interno  

---

*Última atualização: Fevereiro 2026*
