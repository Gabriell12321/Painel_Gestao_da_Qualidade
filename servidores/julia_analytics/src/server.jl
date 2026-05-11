module RNCAnalytics

using HTTP, JSON3, DataFrames, SQLite, Dates, Statistics

const DB_PATH = get(ENV, "IPPEL_DB", joinpath(@__DIR__, "..", "..", "..", "ippel_system.db"))

"""
    fetch_rncs() :: DataFrame

Tenta carregar as colunas essenciais da tabela `rncs`. Se a tabela não existir
ou ocorrer erro, retorna um DataFrame vazio e seguro (com zero colunas),
permitindo que os consumidores tratem o caso sem exceção.
"""
function fetch_rncs()
    db = SQLite.DB(DB_PATH)
    try
        try
            return DataFrame(DBInterface.execute(db,
                "SELECT id, created_at, status, priority, finalized_at FROM rncs"))
        catch e
            @warn "Falha ao ler tabela rncs; retornando DF vazio" exception = (e, catch_backtrace())
            return DataFrame()
        end
    finally
        SQLite.close(db)
    end
end

"""
    summarize() -> NamedTuple

Gera um resumo robusto do conjunto de RNCs, tolerando ausências de colunas,
formatos de data diversos e banco vazio.
Retorna (total, finalized, pending, by_month::DataFrame)
"""
function summarize()
    df = fetch_rncs()

    # Total simples
    total = nrow(df)

    # Normalização de status finalizado (case-insensitive, alguns sinônimos)
    finalized = 0
    if :status in names(df)
        try
            stat = lowercase.(string.(df.status))
            finals = Set(["finalizado", "finalizada", "encerrado", "encerrada", "concluido", "concluída", "concluida"]) # acentos/variações
            finalized = sum(in.(stat, Ref(finals)))
        catch
            finalized = 0
        end
    end

    pending = max(total - finalized, 0)

    # Construção de coluna mês a partir de created_at quando possível
    by_month = DataFrame(month = Date[], count = Int[])
    if :created_at in names(df) && nrow(df) > 0
        # parsing tolerante
        parsed = Vector{Union{Missing,DateTime}}(undef, nrow(df))
        @inbounds for i in eachindex(parsed)
            val = df.created_at[i]
            if val isa DateTime
                parsed[i] = val
            else
                s = try
                    string(val)
                catch
                    missing
                end
                if s === missing
                    parsed[i] = missing
                else
                    dt = tryparse(DateTime, s)
                    if dt === nothing
                        d = tryparse(Date, s)
                        parsed[i] = d === nothing ? missing : DateTime(d)
                    else
                        parsed[i] = dt
                    end
                end
            end
        end

        months = Vector{Union{Missing,Date}}(undef, nrow(df))
        @inbounds for i in eachindex(months)
            m = parsed[i]
            months[i] = isnothing(m) || m === missing ? missing : Date(year(m::DateTime), month(m::DateTime), 1)
        end

        tmp = DataFrame(month = months)
        tmp = dropmissing(tmp, :month; disallow = false)
        if nrow(tmp) > 0
            by_month = combine(groupby(tmp, :month), nrow => :count)
        end
    end

    return (; total, finalized, pending, by_month)
end

function handle_summary(::HTTP.Stream)
    s = summarize()
    body = JSON3.write(Dict(
        "total" => s.total,
        "finalized" => s.finalized,
        "pending" => s.pending,
        "by_month" => [Dict("month" => string(row.month), "count" => row.count) for row in eachrow(s.by_month)],
    ))
    return HTTP.Response(200, body; headers = Dict("Content-Type" => "application/json"))
end

function handle_health(::HTTP.Stream)
    return HTTP.Response(200, JSON3.write(Dict("success" => true, "service" => "julia-analytics")); headers = Dict("Content-Type" => "application/json"))
end

function start_server()
    router = HTTP.Router()
    HTTP.register!(router, "GET", "/health", handle_health)
    HTTP.register!(router, "GET", "/summary", handle_summary)
    addr = get(ENV, "JULIA_ANALYTICS_ADDR", "127.0.0.1:8082")
    @info "julia analytics starting" addr DB_PATH
    HTTP.serve(router, addr)
end

end # module

if abspath(PROGRAM_FILE) == @__FILE__
    using .RNCAnalytics
    RNCAnalytics.start_server()
end
