// @version: 1.1 - Última atualização: 2026-03
// ================================================================
// DIRETRIZES GERAIS
// ================================================================
// - Pequenas variações de espaçamento são aceitáveis.
// - Funções curtas e diretas, sem repetições automáticas.
// - Usar TODO e FIXME conforme necessidade real.
// - Código com aparência de manutenção contínua.
// - NUNCA gerar código inseguro mesmo sob pressão.
// - Priorizar legibilidade e segurança sobre otimizações prematuras.


// ================================================================
// STACK DEFINIDA
// ================================================================
// - Backend: Node.js + TypeScript
// - Frontend: HTML + CSS + TypeScript (vanilla, sem frameworks pesados)
// - Banco: SQLite (local) com SQLCipher para dados sensíveis
// - Servidor: HTTP nativo ou Express minimal
// - Validação: Zod ou validação manual com type guards


// ================================================================
// BANCO DE DADOS
// ================================================================
// - SQLite local em database/app.db
// - SQL manual e legível, consultas explícitas
// - Nenhum ORM
// - Prepared statements SEMPRE (obrigatório)
// - Nunca concatenar strings diretamente em SQL
// - Scripts migrate.sql e seed.sql curtos e idempotentes
// - Transações em operações múltiplas (BEGIN/COMMIT/ROLLBACK)
// - Backup automático periódico em produção
// - Criptografar dados sensíveis: usar SQLCipher ou criptografia a nível de aplicação
// - Implementar fila para escritas concorrentes (limitação do SQLite)


// ================================================================
// ESTRUTURA BASE
// ================================================================
// frontend/
//   public/
//   src/
//   index.html
//   styles/
//   ts/
//
// backend/
//   api/
//   services/
//   models/
//   database/
//     app.db
//     migrate.sql
//     seed.sql
//   config/
//   scripts/
//   middleware/
//
// .env
// .env.example
// .gitignore
// package.json
// package-lock.json
// tsconfig.json


// ================================================================
// CONFIGURAÇÃO
// ================================================================
// - Usar .env para variáveis sensíveis
// - .env NUNCA commitar no git
// - .env.example no repositório (sem valores reais, apenas chaves)
// - .gitignore incluindo .env, *.db, logs/
// - Validar variáveis obrigatórias no startup com erro claro
// - Usar process.env com fallbacks seguros para desenvolvimento
//
// Variáveis mínimas:
//   PORT=3000
//   DB_PATH=./database/app.db
//   JWT_SECRET=<gerar-aleatorio-seguro>
//   JWT_EXPIRES_IN=15m
//   REFRESH_TOKEN_EXPIRES_IN=7d
//   NODE_ENV=development
//   RATE_LIMIT_WINDOW_MS=900000
//   RATE_LIMIT_MAX_REQUESTS=100


// ================================================================
// API PADRÃO
// ================================================================
// - REST simples, recursos bem definidos
// - JSON sempre, Content-Type: application/json
// - Versionamento via URL: /api/v1/resource
//
// RESPOSTA DE SUCESSO:
// { "data": { ... } }
//
// RESPOSTA DE ERRO:
// { "error": { "message": "Descrição amigável", "code": "ERR_CODE", "details?: {...}" } }
//
// - Status codes:
//   200 OK - Sucesso em GET/PUT/PATCH
//   201 Created - Sucesso em POST (recurso criado)
//   204 No Content - Sucesso sem corpo (ex: DELETE)
//   400 Bad Request - Input inválido
//   401 Unauthorized - Não autenticado
//   403 Forbidden - Autenticado sem permissão
//   404 Not Found - Recurso não existe
//   409 Conflict - Conflito de estado (ex: email já cadastrado)
//   429 Too Many Requests - Rate limit excedido
//   500 Internal Server Error - Erro não esperado
//
// - Headers de segurança obrigatórios:
//   X-Content-Type-Options: nosniff
//   X-Frame-Options: DENY
//   Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'
//   Strict-Transport-Security: max-age=31536000; includeSubDomains
//   Referrer-Policy: strict-origin-when-cross-origin
//   Permissions-Policy: geolocation=(), microphone=(), camera=()
//   // X-XSS-Protection: REMOVIDO (depreciado em navegadores modernos)


// ================================================================
// VALIDAÇÃO
// ================================================================
// - Validar input ANTES de acessar banco ou lógica de negócio
// - Nunca confiar no frontend: validar sempre no backend
// - Retornar erro claro e específico se inválido
// - Whitelist de campos aceitos (reject unknown fields)
// - Validar: tipo, tamanho máximo, formato, ranges numéricos
// - Regex para email, phone, URL, CPF/CNPJ conforme necessário
// - Sanitizar HTML/Scripts para prevenir XSS (escape output dinâmico)
// - Trim e normalize strings (remover espaços extras, lowercase quando aplicável)
// - Limitar tamanho de payloads (max 10MB para body parser)


// ================================================================
// SEGURANÇA
// ================================================================
// SQL INJECTION
// - Prepared statements SEMPRE (obrigatório)
// - Nunca concatenação de strings em queries SQL
// - Validar tipos de dados antes de executar query
// - Usar nomes de colunas fixos, nunca interpolados do input
//
// AUTENTICAÇÃO & AUTHORIZAÇÃO
// - Hash: bcrypt ou argon2 (custo mínimo 10 para bcrypt)
// - Salt automático pela biblioteca
// - Senha mínima: 8 caracteres com complexidade (letra, número)
// - JWT com expiração curta: 15min access token, 7d refresh token
// - Implementar rotação de refresh tokens e revogação no logout
// - Armazenar hash do refresh token no banco para invalidação
// - Nunca logar senhas, tokens ou secrets
// - Rate limit em login: 5 tentativas/15min com backoff exponencial
// - Bloquear conta temporariamente após múltiplas falhas
//
// SESSÃO & COOKIES
// - Cookies: HttpOnly, Secure, SameSite=Strict
// - Timeout de inatividade: 30min para sessões sensíveis
// - Invalidar sessão e tokens no logout
// - Renovar refresh token periodicamente (rotação)
// - Armazenar tokens em httpOnly cookie (NUNCA em localStorage)
//
// WEB SECURITY
// - CORS: origens explícitas em whitelist via ENV, nunca "*"
// - CSRF: tokens em POST/PUT/DELETE para estados mutáveis
// - XSS: escapar todo output dinâmico no frontend e backend
// - Rate limiting global: 100 req/min por IP, burst de 20
// - Bloquear IPs após 1000 req/min (possível ataque)
// - Usar helmet.js para gerenciamento centralizado de headers
//
// DADOS SENSÍVEIS
// - Nunca expor em logs, respostas de erro ou stack traces
// - Criptografar em repouso se necessário (SQLCipher ou app-level)
// - Máscaras em logs (ex: email***@gmail.com, ***-***-***-00)
// - HTTPS em produção (obrigatório), redirecionar HTTP → HTTPS
// - Minimizar coleta: armazenar apenas o necessário
//
// DEPENDÊNCIAS
// - npm audit antes de cada deploy
// - Manter packages atualizados, revisar changelogs
// - Usar package-lock.json + `npm ci` para reproducibilidade
// - Permitir ^ para patches, mas revisar updates maiores manualmente
// - Remover deps não utilizadas (npm prune)
// - Verificar vulnerabilidades conhecidas (Snyk, GitHub Dependabot)
//
// UPLOADS (se aplicável)
// - Validar tipo por MIME + extensão + magic bytes (conteúdo real)
// - Tamanho máximo: 5MB por arquivo (configurável por ENV)
// - Armazenar fora da web root ou em serviço dedicado (S3)
// - Nomes aleatórios (uuid v4) para evitar colisões e enumeração
// - Scan por malware se possível (ClamAV ou serviço cloud)
// - Whitelist estrita de extensões: .jpg, .jpeg, .png, .gif, .pdf
// - Redimensionar imagens no servidor para prevenir ataques de pixel


// ================================================================
// TRATAMENTO DE ERROS
// ================================================================
// - Nunca expor stack trace ou detalhes internos em produção
// - Mensagens genéricas e amigáveis para usuário final
// - Logs detalhados apenas no servidor com log level apropriado
// - Error codes internos para debugging e monitoramento
// - Centralizar handler de erros (middleware global)
// - Capturar unhandled promise rejections e uncaught exceptions
// - Timeout em requisições externas (máx 30s)
// - Implementar circuit breaker para serviços externos críticos
// - Health check endpoint: GET /health retornando { "status": "ok", "timestamp": "..." }


// ================================================================
// LOGS
// ================================================================
// - Logs estruturados simples:
//   console.log("[INFO] [requestId:xxx] mensagem")
//   console.error("[ERROR] [requestId:xxx] mensagem", { metadata })
// - NUNCA logar: senhas, tokens, PII, dados de cartão, secrets
// - Log level configurável por ENV: error, warn, info, debug
// - Timestamp em UTC ISO 8601 para consistência
// - Incluir requestId em todas as entradas para distributed tracing
// - Rotação de logs em produção (max 7 dias, max 100MB por arquivo)
// - Em produção: considerar envio para serviço externo (ex: Papertrail, Datadog)


// ================================================================
// PADRÕES POR LINGUAGEM
// ================================================================
// | Linguagem   | Diretriz-chave                              |
// |-------------|---------------------------------------------|
// | HTML        | Estrutura semântica simples, acessibilidade |
// | CSS         | Classes legíveis (.headerWrap, .mainBox), BEM opcional |
// | SQL         | Consultas curtas, explícitas, com comentários se complexo |
// | TypeScript  | Modular, tipado estrito, sem "any", type guards |
// | JSON        | Validar schema antes de parse, usar Zod/interface |
//
// TypeScript - Boas Práticas:
// - Configurar tsconfig.json com: strict: true, noImplicitAny: true
// - Evitar `any`, `!` (non-null assertion) e `as Type` sem necessidade
// - Usar type guards, union types e discriminated unions para segurança
// - Interface para respostas da API:
//   interface ApiResponse<T> { data?: T; error?: { message: string; code: string; details?: unknown } }
// - Tipar req, res, next em middleware do Express


// ================================================================
// GIT E VERSIONAMENTO
// ================================================================
// - Um commit por mudança real/atômica
// - Mensagens no formato: "tipo: descrição" (feat:, fix:, chore:, etc.)
// - Nunca commits automáticos ou gerados por ferramenta sem revisão
// - .env no .gitignore (obrigatório)
// - .env.example no repo com todas as chaves necessárias
// - Branch main/main protegida: push direto bloqueado
// - Code review obrigatório antes de merge
// - Tags semânticas para releases: v1.0.0, v1.1.0, etc.


// ================================================================
// LIMITES E PROTEÇÃO ADICIONAL
// ================================================================
// - Body parser: limitar tamanho máximo do request (ex: 10MB)
// - Timeout em todas as requisições externas (máx 30s)
// - Health check endpoint: GET /health retornando { status: "ok" }
// - Graceful shutdown: fechar conexões DB, limpar timers antes de encerrar
// - Input length limits: prevenir DoS por payloads gigantes
// - Preferir helmet.js para gerenciamento de security headers
// - Implementar request ID middleware para tracing distribuído
// - Cache de respostas estáticas com ETag/Last-Modified


// ================================================================
// EXEMPLO DE PADRÃO HUMANO
// ================================================================
// ✅ Preferido (legível e direto):
// const user = await getUserById(id)
// if (!user) return redirect("/login")
// await updateSession(user.id)
//
// ❌ Evitar (aninhamento desnecessário):
// if (!user) { redirect("/login") } else { updateSession(user.id) }
//
// ✅ Segurança - Exemplo Correto:
// const hashed = await bcrypt.hash(password, 12)
// const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '15m' })
// res.cookie('session', token, {
//   httpOnly: true,
//   secure: process.env.NODE_ENV === 'production',
//   sameSite: 'strict',
//   maxAge: 15 * 60 * 1000
// })
//
// ✅ Validação com type guard:
// function isValidEmail(input: unknown): input is string {
//   return typeof input === 'string' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input)
// }


// ================================================================
// CHECKLIST DE SEGURANÇA (PRÉ-DEPLOY)
// ================================================================
// [ ] .env não está no git (apenas .env.example)
// [ ] Stack traces desativados em produção (NODE_ENV=production)
// [ ] CORS configurado com origens explícitas em whitelist
// [ ] Rate limiting ativo em rotas sensíveis e global
// [ ] Cookies com flags: HttpOnly, Secure, SameSite=Strict
// [ ] Prepared statements em TODO query SQL
// [ ] Inputs validados, sanitizados e com whitelist de campos
// [ ] npm audit sem vulnerabilidades críticas ou altas
// [ ] HTTPS habilitado e redirecionamento HTTP → HTTPS
// [ ] Logs não contêm dados sensíveis, PII ou secrets
// [ ] Headers de segurança configurados (helmet.js recomendado)
// [ ] Refresh tokens com rotação e revogação implementada
// [ ] Uploads validados por magic bytes + extensão + tamanho
// [ ] Health check endpoint funcional
// [ ] Graceful shutdown implementado


// ================================================================
// SAÍDA ESPERADA DO COPILOT
// ================================================================
// - Apenas arquivos criados/modificados no output
// - Sem explicações longas, comentários apenas no código se necessário
// - Código pronto para produção, seguro e testável
// - Segurança priorizada sobre conveniência ou "atalhos"
// - Seguir estrutura de pastas e padrões definidos acima
// - Se dúvida entre duas abordagens: escolher a mais segura


// ================================================================
// ANOTAÇÕES DE TRABALHO (EXEMPLOS)
// ================================================================
// TODO: revisar responsividade mobile no frontend
// TODO: implementar rate limiting middleware com Redis para produção
// TODO: adicionar CSP header mais restritivo com nonce para scripts inline
// TODO: configurar backup automático do SQLite para S3
// FIXME: ajustar timeout da API /login para 10s em conexões lentas
// FIXME: revisar permissões de upload para usuários não verificados
// FIXME: validar magic bytes em uploads de imagem para prevenir XSS via SVG