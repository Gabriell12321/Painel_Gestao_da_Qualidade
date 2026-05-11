# 🏗️ Nova Estrutura do Projeto IPPEL RNC

**Atualizado:** Fevereiro de 2026

---

## 📁 Estrutura de Diretórios

```
Z:\rnc pdc\
│
├── 📄 server_form.py                 # Servidor principal Flask (Python)
├── 📄 main_system.py                 # Sistema alternativo
├── 📄 ippel_system.db                # Banco de dados SQLite
│
├── 🚀 MICROSERVIÇOS (12 linguagens)
├── ─────────────────────────────────
├── 🦀 rust_images/                   # Porta 8081 - Rust (Processamento imagens)
├── 🔬 julia_analytics/               # Porta 8082 - Julia (Analytics)
├── 🐹 go_reports/                    # Porta 8083 - Go (PDFs)
├── 🎯 kotlin_utils/                  # Porta 8084 - Kotlin (QR codes)
├── 🍎 swift_tools/                   # Porta 8085 - Swift (Hash/Crypto)
├── ⚡ scala_tools/                   # Porta 8086 - Scala (Base64)
├── 🌟 nim_tools/                     # Porta 8087 - Nim (UUID/Tokens)
├── 📜 v_tools/                       # Porta 8088 - V (Slugify)
├── ƛ haskell_tools/                  # Porta 8089 - Haskell (Levenshtein)
├── 🎯 zig_tools/                     # Porta 8090 - Zig (XXH3)
├── 💎 crystal_tools/                 # Porta 8091 - Crystal (SHA256)
├── 🦕 deno_tools/                    # Porta 8092 - Deno/TS (URL encode/decode)
│
├── 🔧 services/                      # Serviços Python (apenas código Python)
│   ├── db.py                         # Pool de conexões
│   ├── cache.py                      # Cache system
│   ├── permissions.py                # Permissões
│   ├── users.py                      # Gestão de usuários
│   ├── rnc.py                        # Lógica de RNCs
│   ├── jwt_auth.py                   # JWT tokens
│   ├── lockout.py                    # Progressive lockout
│   ├── security_log.py               # Security logging
│   ├── notifications_api.py          # Notificações REST
│   ├── notification_socketio.py      # WebSocket notifications
│   ├── validation.py                 # Validação de dados
│   ├── pagination.py                 # Paginação
│   ├── pdf_generator.py              # Geração de PDFs
│   ├── image_utils.py                # Processamento de imagens
│   ├── database_optimizer.py         # Otimização DB
│   └── ... (outros serviços Python)
│
├── 🛣️ routes/                        # Blueprints Flask
│   ├── api.py                        # APIs gerais
│   ├── auth.py                       # Autenticação
│   ├── rnc.py                        # CRUD de RNCs
│   ├── admin.py                      # Administração
│   ├── report.py                     # Relatórios
│   └── print_reports.py              # Impressão
│
├── 🎨 templates/                     # Templates HTML
│   ├── dashboard_improved.html       # Dashboard principal (23.4k linhas)
│   ├── new_rnc.html                  # Formulário de RNC
│   ├── view_rnc.html                 # Visualização de RNC
│   ├── login.html                    # Login
│   └── reports/                      # Relatórios
│
├── 🖼️ static/                        # Assets frontend
│   ├── css/                          # Estilos
│   ├── js/                           # JavaScript
│   ├── uploads/                      # Uploads de usuários
│   └── avatars/                      # Avatares
│
├── ⚛️ src/                           # Frontend React/TypeScript
│   ├── components/                   # Componentes React
│   ├── hooks/                        # React Hooks
│   └── utils/                        # Utilitários
│
├── 📚 docs/                          # Documentação
│   ├── SECURITY_GUIDE.md             # Guia de segurança
│   ├── API_GUIDE.md                  # Guia de APIs
│   ├── DEPLOYMENT_GUIDE.md           # Guia de deploy
│   ├── README.md                     # README principal
│   └── ... (50+ arquivos .md)
│
├── 🧪 tests/                         # Testes (150+ arquivos)
│   ├── test_api.py
│   ├── test_auth.py
│   ├── test_rnc.py
│   └── ...
│
├── 📝 migrations/                    # Migrações de banco
├── 📊 logs/                          # Logs do sistema
├── 💾 backups/                       # Backups do banco
└── 📖 DOCUMENTACAO_COMPLETA.md       # Documentação completa
```

---

## 📊 Resumo por Categoria

### **Servidor Principal**
- `server_form.py` - 10.941 linhas (Python/Flask)
- `main_system.py` - 2.858 linhas (Python/Flask)

### **Microserviços (12 linguagens)**
| Linguagem | Diretório | Porta | Finalidade |
|-----------|-----------|-------|------------|
| Rust | `rust_images/` | 8081 | Processamento de imagens |
| Julia | `julia_analytics/` | 8082 | Analytics estatístico |
| Go | `go_reports/` | 8083 | Geração de PDFs |
| Kotlin | `kotlin_utils/` | 8084 | QR codes (ZXing) |
| Swift | `swift_tools/` | 8085 | Hash/criptografia |
| Scala | `scala_tools/` | 8086 | Base64 encode/decode |
| Nim | `nim_tools/` | 8087 | UUID/token generation |
| V | `v_tools/` | 8088 | Slugify |
| Haskell | `haskell_tools/` | 8089 | Levenshtein distance |
| Zig | `zig_tools/` | 8090 | XXH3 hash |
| Crystal | `crystal_tools/` | 8091 | SHA256 |
| Deno | `deno_tools/` | 8092 | URL encode/decode |

### **Serviços Python (services/)**
- 30+ arquivos Python com serviços auxiliares
- Clientes para conectar aos microserviços
- Sistema de cache, permissões, notificações, etc.

### **Frontend**
- `templates/` - 50+ templates HTML
- `static/` - CSS, JavaScript, uploads
- `src/` - React + TypeScript (novo frontend)

### **Documentação**
- 123 arquivos `.md`
- 4 guias principais (Security, API, Deployment, Microservices)
- 50+ READMEs especializados

---

## 🎯 Vantagens Desta Organização

### **1. Visibilidade**
✅ Microserviços ficam mais evidentes na raiz  
✅ Fácil identificar cada tecnologia  
✅ Separação clara entre Python e outras linguagens

### **2. Acesso Rápido**
✅ Build e debug mais ágeis  
✅ Paths mais curtos  
✅ Menos navegação em subdiretórios

### **3. Independência**
✅ Cada microserviço pode ser gerenciado separadamente  
✅ Build individual sem afetar outros  
✅ Versionamento independente se necessário

### **4. Clareza Arquitetural**
✅ `server_form.py` permanece como ponto principal de entrada  
✅ `services/` contém apenas código Python  
✅ Microserviços polyglot na raiz destacam a arquitetura híbrida

### **5. Manutenibilidade**
✅ Mais fácil adicionar novos microserviços  
✅ Estrutura consistente para todas as linguagens  
✅ Documentação unificada (`MICROSERVICES.md`)

---

## 🔄 Fluxo de Desenvolvimento

### **Desenvolvimento Principal (Python)**
```bash
# Servidor principal
python server_form.py

# Porta: 5001
# Acesso: http://localhost:5001
```

### **Desenvolvimento de Microserviços**
```bash
# Rust
cd rust_images && cargo run --release

# Go
cd go_reports && go run main.go

# Kotlin
cd kotlin_utils && .\gradlew.bat run

# ... (cada um em seu diretório)
```

### **Testes de Integração**
O sistema principal se conecta automaticamente aos microserviços ativos:
- Detecta quais serviços estão online
- Usa fallback Python se serviço estiver offline
- Logs de conexão/desconexão

---

## 📝 Notas Importantes

### **Opcionalidade**
- ✅ **Todos os 12 microserviços são opcionais**
- ✅ O sistema funciona 100% sem nenhum microserviço
- ✅ Cada serviço tem fallback em Python

### **Comunicação**
- ✅ REST APIs entre serviços
- ✅ Timeouts configurados (evita bloqueio)
- ✅ Retry automático com backoff

### **Build**
- ✅ Cada microserviço tem seu próprio build system
- ✅ Não há dependências entre microserviços
- ✅ Podem ser buildados independentemente

### **Deploy**
- ✅ Deploy independente por serviço
- ✅ Health checks individuais
- ✅ Restart automático (systemd/Docker)

---

## 🚀 Comandos Úteis

### **Listar Microserviços**
```bash
# Windows
dir /b | findstr /i "rust julia go kotlin swift scala nim v haskell zig crystal deno"

# Linux/Mac
ls -d */ | grep -E "rust|julia|go|kotlin|swift|scala|nim|v|haskell|zig|crystal|deno"
```

### **Verificar Portas**
```bash
# Windows
netstat -ano | findstr :8081
netstat -ano | findstr :8082
# ... (repetir para cada porta)
```

### **Health Check Geral**
```bash
# Testar todos os serviços
for port in 8081 8082 8083 8084 8085 8086 8087 8088 8089 8090 8091 8092; do
  curl -s http://localhost:$port/health
done
```

---

## 📚 Documentação Relacionada

- **`MICROSERVICES.md`** - Guia completo de inicialização
- **`DOCUMENTACAO_COMPLETA.md`** - Visão geral do sistema
- **`docs/API_GUIDE.md`** - APIs de todos os serviços
- **`docs/DEPLOYMENT_GUIDE.md`** - Guia de deploy em produção

---

*Estrutura do Projeto - Fevereiro 2026*
