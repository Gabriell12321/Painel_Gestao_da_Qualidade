# 🚀 Servidores IPPEL - Guia Completo

**Versão:** 1.0.0  
**Data:** Fevereiro de 2026  

---

## 📋 Visão Geral

Este documento descreve a organização e inicialização dos **servidores do Sistema IPPEL RNC**, incluindo o servidor principal e os 12 microserviços polyglot.

---

## 📁 Estrutura de Servidores

```
Z:\rnc pdc\
│
├── 📄 server_form.py              # Servidor Principal (Python/Flask)
│                                   # Porta: 5001
│                                   # NÃO MOVER - Permanece na raiz
│
└── 📂 servidores/                 # ← Pasta com TODOS os microserviços
    │
    ├── 🦀 rust_images/            # Porta 8081
    ├── 🔬 julia_analytics/        # Porta 8082
    ├── 🐹 go_reports/             # Porta 8083
    ├── 🎯 kotlin_utils/           # Porta 8084
    ├── 🍎 swift_tools/            # Porta 8085
    ├── ⚡ scala_tools/            # Porta 8086
    ├── 🌟 nim_tools/              # Porta 8087
    ├── 📜 v_tools/                # Porta 8088
    ├── ƛ haskell_tools/           # Porta 8089
    ├── 🎯 zig_tools/              # Porta 8090
    ├── 💎 crystal_tools/          # Porta 8091
    └── 🦕 deno_tools/             # Porta 8092
```

---

## 🎯 Servidor Principal

### **server_form.py** ✅
- **Localização:** `Z:\rnc pdc\server_form.py` (NÃO MOVER)
- **Porta:** 5001
- **Tecnologia:** Python/Flask
- **Linhas:** 10.941
- **Status:** ✅ Produção

**Inicialização:**
```bash
cd Z:\rnc pdc
python server_form.py
```

**Acesso:** http://localhost:5001

---

## 🚀 Microserviços (na pasta `servidores/`)

### Resumo dos 12 Microserviços

| # | Microserviço | Porta | Linguagem | Finalidade |
|---|--------------|-------|-----------|------------|
| 1 | **rust_images** | 8081 | Rust | Processamento de imagens |
| 2 | **julia_analytics** | 8082 | Julia | Analytics estatístico |
| 3 | **go_reports** | 8083 | Go | Geração de PDFs |
| 4 | **kotlin_utils** | 8084 | Kotlin | QR codes (ZXing) |
| 5 | **swift_tools** | 8085 | Swift | Hash/criptografia |
| 6 | **scala_tools** | 8086 | Scala | Base64 encode/decode |
| 7 | **nim_tools** | 8087 | Nim | UUID/token generation |
| 8 | **v_tools** | 8088 | V | Slugify |
| 9 | **haskell_tools** | 8089 | Haskell | Levenshtein distance |
| 10 | **zig_tools** | 8090 | Zig | XXH3 hash |
| 11 | **crystal_tools** | 8091 | Crystal | SHA256 |
| 12 | **deno_tools** | 8092 | Deno/TS | URL encode/decode |

---

## 🔧 Inicialização Individual

### 1. Rust Images (8081)
```bash
cd Z:\rnc pdc\servidores\rust_images
cargo run --release
```

### 2. Julia Analytics (8082)
```bash
cd Z:\rnc pdc\servidores\julia_analytics
julia --project src/main.jl
```

### 3. Go Reports (8083)
```bash
cd Z:\rnc pdc\servidores\go_reports
go run main.go
```

### 4. Kotlin Utils (8084)
```bash
cd Z:\rnc pdc\servidores\kotlin_utils
.\gradlew.bat run
```

### 5. Swift Tools (8085)
```bash
cd Z:\rnc pdc\servidores\swift_tools
swift run
```

### 6. Scala Tools (8086)
```bash
cd Z:\rnc pdc\servidores\scala_tools
sbt run
```

### 7. Nim Tools (8087)
```bash
cd Z:\rnc pdc\servidores\nim_tools
nim c -r -d:release src/nim_tools.nim
```

### 8. V Tools (8088)
```bash
cd Z:\rnc pdc\servidores\v_tools
v run src/main.v
```

### 9. Haskell Tools (8089)
```bash
cd Z:\rnc pdc\servidores\haskell_tools
stack run
```

### 10. Zig Tools (8090)
```bash
cd Z:\rnc pdc\servidores\zig_tools
zig build run
```

### 11. Crystal Tools (8091)
```bash
cd Z:\rnc pdc\servidores\crystal_tools
crystal run src/main.cr --release
```

### 12. Deno Tools (8092)
```bash
cd Z:\rnc pdc\servidores\deno_tools
deno run --allow-net server.ts
```

---

## 🎛️ Inicialização em Lote

### Script PowerShell - Todos os Servidores

Criar arquivo `iniciar_todos_servidores.ps1`:

```powershell
# iniciar_todos_servidores.ps1

Write-Host "🚀 Iniciando todos os servidores IPPEL..." -ForegroundColor Green

# Servidor Principal (Python)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; python server_form.py"
Start-Sleep -Seconds 3

# Microserviços
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\servidores\rust_images'; cargo run --release"
Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\servidores\go_reports'; go run main.go"
Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\servidores\kotlin_utils'; .\gradlew.bat run"
Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\servidores\deno_tools'; deno run --allow-net server.ts"

Write-Host "✅ Servidores inicializados!" -ForegroundColor Green
Write-Host "📊 Portas: 5001 (principal), 8081-8092 (microserviços)" -ForegroundColor Yellow
```

**Executar:**
```powershell
.\iniciar_todos_servidores.ps1
```

---

## 🛑 Parar Servidores

### Servidor Principal
```bash
# Ctrl+C no terminal onde está rodando
```

### Microserviços
```bash
# Ctrl+C em cada terminal

# Ou PowerShell (forçar)
Get-Process | Where-Object {
    $_.ProcessName -match 'rust|julia|go|java|swift|nim|v|stack|zig|crystal|deno'
} | Stop-Process -Force
```

---

## 🧪 Testar Conectividade

### Health Check

```bash
# Servidor Principal
curl http://localhost:5001/api/health

# Microserviços
curl http://localhost:8081/health
curl http://localhost:8082/health
curl http://localhost:8083/health
# ... (repetir para cada porta até 8092)
```

### Teste de Integração

O servidor principal (`server_form.py`) detecta automaticamente quais microserviços estão ativos e usa fallback Python para os que estiverem offline.

---

## 📊 Monitoramento

### Verificar Portas (Windows)
```bash
netstat -ano | findstr :5001   # Servidor principal
netstat -ano | findstr :8081   # Rust
netstat -ano | findstr :8082   # Julia
netstat -ano | findstr :8083   # Go
# ... (repetir para cada porta)
```

### Logs

- **Servidor Principal:** `logs/ippel_system.log`
- **Microserviços:** Cada um em seu diretório específico

---

## ⚠️ Troubleshooting

### Porta Já em Uso
```bash
# Windows
netstat -ano | findstr :8081
taskkill /PID <PID> /F
```

### Dependências Faltando
```bash
# Rust
cd servidores\rust_images
cargo update

# Go
cd servidores\go_reports
go mod tidy

# Kotlin
cd servidores\kotlin_utils
.\gradlew.bat build --refresh-dependencies
```

### Erro de Compilação
```bash
# Limpar build
cd servidores\rust_images && cargo clean
cd servidores\go_reports && go clean
cd servidores\kotlin_utils && .\gradlew.bat clean
```

---

## 📝 Variáveis de Ambiente

### Configurar Endereços

No `server_form.py`, os clientes Python usam:

```bash
RUST_IMAGES_URL=http://localhost:8081
JULIA_ANALYTICS_URL=http://localhost:8082
GO_REPORTS_URL=http://localhost:8083
KOTLIN_UTILS_URL=http://localhost:8084
SWIFT_TOOLS_URL=http://localhost:8085
SCALA_TOOLS_URL=http://localhost:8086
NIM_TOOLS_URL=http://localhost:8087
V_TOOLS_URL=http://localhost:8088
HASKELL_TOOLS_URL=http://localhost:8089
ZIG_TOOLS_URL=http://localhost:8090
CRYSTAL_TOOLS_URL=http://localhost:8091
DENO_TOOLS_URL=http://localhost:8092
```

---

## 🎯 Considerações Importantes

### ✅ **Opcionalidade**
- **Todos os 12 microserviços são opcionais**
- O sistema principal funciona 100% sem nenhum microserviço
- Cada serviço tem fallback em Python

### ✅ **Organização**
- **`server_form.py`** permanece na raiz (NÃO MOVER)
- **Todos os microserviços** estão em `servidores/`
- **`services/`** contém apenas serviços Python

### ✅ **Comunicação**
- REST APIs entre serviços
- Timeouts configurados (evita bloqueio)
- Retry automático com backoff

---

## 📚 Documentação Relacionada

- **`DOCUMENTACAO_COMPLETA.md`** - Visão geral completa do sistema
- **`docs/API_GUIDE.md`** - Guia completo de APIs
- **`docs/DEPLOYMENT_GUIDE.md`** - Guia de deploy em produção
- **`docs/SECURITY_GUIDE.md`** - Guia de segurança

---

## 🚀 Comandos Úteis

### Listar Todos os Servidores
```bash
# Windows
dir servidores /b

# Verificar servidor principal
dir server_form.py
```

### Verificar Status
```bash
# Windows - Portas em uso
netstat -ano | findstr :5001
netstat -ano | findstr :808
```

### Health Check Geral
```bash
# Testar servidor principal
curl http://localhost:5001/api/health

# Testar microserviços (PowerShell)
$ports = 8081,8082,8083,8084,8085,8086,8087,8088,8089,8090,8091,8092
foreach ($port in $ports) {
    Write-Host "Porta $port :"
    curl -s http://localhost:$port/health
}
```

---

## 📊 Resumo da Estrutura

```
Z:\rnc pdc\
│
├── 📄 server_form.py              ← Servidor Principal (NÃO MOVER)
│
├── 📂 servidores/                 ← Todos os microserviços
│   ├── rust_images/
│   ├── julia_analytics/
│   ├── go_reports/
│   ├── kotlin_utils/
│   ├── swift_tools/
│   ├── scala_tools/
│   ├── nim_tools/
│   ├── v_tools/
│   ├── haskell_tools/
│   ├── zig_tools/
│   ├── crystal_tools/
│   └── deno_tools/
│
└── 📂 services/                   ← Apenas serviços Python
    ├── db.py
    ├── cache.py
    ├── permissions.py
    └── ... (clientes *_client.py)
```

---

*Guia de Servidores - Versão 1.0 - Fevereiro 2026*
