# RNCAnalytics (Julia)

Microserviço Julia para análises do banco SQLite do sistema RNC IPPEL.

## Requisitos
- Julia 1.9+

## Instalação das dependências
No diretório `services/julia_analytics`:

```powershell
julia --project=. -e "using Pkg; Pkg.instantiate();"
```

## Execução
```powershell
julia --project=. src/server.jl
```

Por padrão, o serviço sobe em `127.0.0.1:8082`. Configure com a variável:
- `JULIA_ANALYTICS_ADDR=0.0.0.0:8082`

Para apontar o banco (opcional, senão usa `ippel_system.db` na raiz):
- `IPPEL_DB=g:/My Drive/Trabalhos pendentes/rncs/RELATORIO DE NÃO CONFORMIDADE IPPEL/ippel_system.db`

## Endpoints
- `GET /health` — healthcheck
- `GET /summary` — retorna resumo (total, finalizados, pendentes, agregação por mês)

## Integração no Flask (opcional)
- Defina `JULIA_ANALYTICS_URL=http://127.0.0.1:8082`
- Use a rota proxy `GET /api/analytics/summary`
