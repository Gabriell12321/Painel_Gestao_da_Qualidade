# 🚀 Microserviços IPPEL - Guia de Inicialização

**Versão:** 1.0.0  
**Data:** Fevereiro de 2026  

---

## 📋 Visão Geral

Este documento descreve como inicializar e gerenciar os **12 microserviços polyglot** do Sistema IPPEL RNC, agora localizados na raiz do projeto.

---

## 📦 Localização dos Microserviços

Todos os microserviços estão na **raiz do projeto** `Z:\rnc pdc\`:

```
Z:\rnc pdc\
├── rust_images/           # Porta 8081
├── julia_analytics/       # Porta 8082
├── go_reports/            # Porta 8083
├── kotlin_utils/          # Porta 8084
├── swift_tools/           # Porta 8085
├── scala_tools/           # Porta 8086
├── nim_tools/             # Porta 8087
├── v_tools/               # Porta 8088
├── haskell_tools/         # Porta 8089
├── zig_tools/             # Porta 8090
├── crystal_tools/         # Porta 8091
└── deno_tools/            # Porta 8092
```

---

## 🎯 Status dos Microserviços

| Microserviço | Porta | Status | Inicialização |
|--------------|-------|--------|---------------|
| **rust_images** | 8081 | ✅ Opcional | `cargo run` |
| **julia_analytics** | 8082 | ✅ Opcional | `julia --project src/main.jl` |
| **go_reports** | 8083 | ✅ Opcional | `go run main.go` |
| **kotlin_utils** | 8084 | ✅ Opcional | `.\gradlew.bat run` |
| **swift_tools** | 8085 | ✅ Opcional | `swift run` |
| **nim_tools** | 8087 | ✅ Opcional | `nim c -r src/nim_tools.nim` |
| **v_tools** | 8088 | ✅ Opcional | `v run src/main.v` |
| **haskell_tools** | 8089 | ✅ Opcional | `stack run` |
| **zig_tools** | 8090 | ✅ Opcional | `zig build run` |
| **crystal_tools** | 8091 | ✅ Opcional | `crystal run src/main.cr` |
| **deno_tools** | 8092 | ✅ Opcional | `deno run --allow-net server.ts` |

**Nota:** O sistema principal (`server_form.py`) funciona **100%** mesmo sem nenhum microserviço ativo.

---

## 🔧 Pré-requisitos por Linguagem

### Rust (rust_images)
```bash
# Instalar Rust
rustup install stable

# Verificar instalação
rustc --version
cargo --version
```

### Julia (julia_analytics)
```bash
# Instalar Julia 1.9+
# Download: https://julialang.org/downloads/

# Verificar instalação
julia --version
```

### Go (go_reports)
```bash
# Instalar Go 1.19+
# Download: https://golang.org/dl/

# Verificar instalação
go version
```

### Kotlin (kotlin_utils)
```bash
# JDK 17+ necessário
# Download: https://adoptium.net/

# Verificar instalação
java -version
```

### Swift (swift_tools)
```bash
# Instalar Swift Toolchain (Windows)
# Download: https://www.swift.org/download/

# Verificar instalação
swift --version
```

### Nim (nim_tools)
```bash
# Instalar Nim
# Download: https://nim-lang.org/install.html

# Verificar instalação
nim --version
```

### V (v_tools)
```bash
# Instalar V
git clone https://github.com/vlang/v
cd v
make

# Verificar instalação
v version
```

### Haskell (haskell_tools)
```bash
# Instalar Stack
# Download: https://docs.haskellstack.org/en/stable/install_and_upgrade/

# Verificar instalação
stack --version
```

### Zig (zig_tools)
```bash
# Instalar Zig
# Download: https://ziglang.org/download/

# Verificar instalação
zig version
```

### Crystal (crystal_tools)
```bash
# Instalar Crystal (Windows via WSL ou Docker)
# Download: https://crystal-lang.org/install/

# Verificar instalação
crystal --version
```

### Deno (deno_tools)
```bash
# Instalar Deno
winget install DenoLand.Deno

# Verificar instalação
deno --version
```

---

## 🚀 Inicialização Individual

### 1. Rust Images (8081)
```bash
cd Z:\rnc pdc\rust_images
cargo run --release
```

**Saída esperada:**
```
Listening on http://0.0.0.0:8081
```

### 2. Julia Analytics (8082)
```bash
cd Z:\rnc pdc\julia_analytics
julia --project src/main.jl
```

**Saída esperada:**
```
Julia Analytics Server running on port 8082
```

### 3. Go Reports (8083)
```bash
cd Z:\rnc pdc\go_reports
go run main.go
```

**Saída esperada:**
```
[GIN-debug] Listening and serving HTTP on :8083
```

### 4. Kotlin Utils (8084)
```bash
cd Z:\rnc pdc\kotlin_utils
.\gradlew.bat run
```

**Saída esperada:**
```
Ktor server started on port 8084
```

### 5. Swift Tools (8085)
```bash
cd Z:\rnc pdc\swift_tools
swift run
```

**Saída esperada:**
```
Swift Tools server running on port 8085
```

### 6. Scala Tools (8086)
```bash
cd Z:\rnc pdc\scala_tools
sbt run
```

**Saída esperada:**
```
[info] Running com.ippel.scala_tools.Main
Server started on port 8086
```

### 7. Nim Tools (8087)
```bash
cd Z:\rnc pdc\nim_tools
nim c -r -d:release src/nim_tools.nim
```

**Saída esperada:**
```
Nim Tools server running on port 8087
```

### 8. V Tools (8088)
```bash
cd Z:\rnc pdc\v_tools
v run src/main.v
```

**Saída esperada:**
```
V server running on port 8088
```

### 9. Haskell Tools (8089)
```bash
cd Z:\rnc pdc\haskell_tools
stack run
```

**Saída esperada:**
```
Haskell Tools server running on port 8089
```

### 10. Zig Tools (8090)
```bash
cd Z:\rnc pdc\zig_tools
zig build run
```

**Saída esperada:**
```
Zig server running on port 8090
```

### 11. Crystal Tools (8091)
```bash
cd Z:\rnc pdc\crystal_tools
crystal run src/main.cr --release
```

**Saída esperada:**
```
Crystal server running on port 8091
```

### 12. Deno Tools (8092)
```bash
cd Z:\rnc pdc\deno_tools
deno run --allow-net server.ts
```

**Saída esperada:**
```
Deno server running on port 8092
```

---

## 🎛️ Inicialização em Lote

### Script PowerShell (Windows)

Criar arquivo `start_all_microservices.ps1`:

```powershell
# start_all_microservices.ps1

$ErrorActionPreference = "SilentlyContinue"

Write-Host "🚀 Iniciando todos os microserviços IPPEL..." -ForegroundColor Green

# Rust Images (8081)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\rust_images'; cargo run --release"
Start-Sleep -Seconds 2

# Go Reports (8083)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\go_reports'; go run main.go"
Start-Sleep -Seconds 2

# Kotlin Utils (8084)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\kotlin_utils'; .\gradlew.bat run"
Start-Sleep -Seconds 2

# Deno Tools (8092)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\deno_tools'; deno run --allow-net server.ts"

Write-Host "✅ Microserviços inicializados!" -ForegroundColor Green
Write-Host "📊 Portas: 8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088, 8089, 8090, 8091, 8092" -ForegroundColor Yellow
```

**Executar:**
```powershell
.\start_all_microservices.ps1
```

---

## 🛑 Parar Microserviços

### Individual
```bash
# Pressionar Ctrl+C em cada terminal
```

### Todos (PowerShell)
```powershell
# Parar todos os processos
Get-Process | Where-Object {
    $_.ProcessName -match 'rust|julia|go|java|swift|nim|v|stack|zig|crystal|deno'
} | Stop-Process -Force
```

---

## 🧪 Testar Conectividade

### Health Check de Cada Serviço

```bash
# Rust Images
curl http://localhost:8081/health

# Julia Analytics
curl http://localhost:8082/health

# Go Reports
curl http://localhost:8083/health

# Kotlin Utils
curl http://localhost:8084/health

# Swift Tools
curl http://localhost:8085/health

# Scala Tools
curl http://localhost:8086/health

# Nim Tools
curl http://localhost:8087/health

# V Tools
curl http://localhost:8088/health

# Haskell Tools
curl http://localhost:8089/health

# Zig Tools
curl http://localhost:8090/health

# Crystal Tools
curl http://localhost:8091/health

# Deno Tools
curl http://localhost:8092/health
```

**Resposta esperada:**
```json
{
  "success": true,
  "service": "nome-serviço",
  "status": "online"
}
```

---

## 📊 Monitoramento

### Verificar Portas em Uso (Windows)
```bash
netstat -ano | findstr :8081
netstat -ano | findstr :8082
# ... repetir para cada porta
```

### Logs por Serviço

Cada serviço gera logs em seu diretório:
- `rust_images/target/`
- `julia_analytics/logs/`
- `go_reports/`
- `kotlin_utils/build/`
- etc.

---

## ⚠️ Troubleshooting

### Porta Já em Uso
```bash
# Windows: Matar processo na porta
netstat -ano | findstr :8081
taskkill /PID <PID> /F
```

### Dependências Faltando
```bash
# Rust
cargo update

# Go
go mod tidy

# Kotlin
.\gradlew.bat build --refresh-dependencies

# Haskell
stack update
stack build
```

### Erro de Compilação
```bash
# Limpar build
cargo clean      # Rust
go clean         # Go
gradlew clean    # Kotlin
stack clean      # Haskell
```

---

## 📝 Variáveis de Ambiente

### Configurar Endereços

No `server_form.py`, os clientes Python usam estas variáveis:

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

## 🎯 Considerações de Produção

### Opcionalidade
- **Todos os serviços são opcionais**
- O sistema principal funciona sem eles
- Cada serviço tem fallback em Python

### Performance
- Inicializar apenas serviços necessários
- Usar `--release` para builds de produção
- Configurar restart automático (systemd/Docker)

### Segurança
- Restringir acesso às portas (firewall)
- Usar HTTPS em produção
- Implementar autenticação entre serviços

---

## 📚 Recursos Adicionais

- **Documentação Principal:** `DOCUMENTACAO_COMPLETA.md`
- **Guia de Deploy:** `docs/DEPLOYMENT_GUIDE.md`
- **Guia de APIs:** `docs/API_GUIDE.md`
- **Guia de Segurança:** `docs/SECURITY_GUIDE.md`

---

*Guia de Microserviços - Versão 1.0 - Fevereiro 2026*
