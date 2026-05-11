# Runs the Julia analytics service
param(
  [string]$Addr = "127.0.0.1:8082",
  [string]$Db = ""
)

$env:JULIA_ANALYTICS_ADDR = $Addr
if ($Db -ne "") { $env:IPPEL_DB = $Db }

julia --project=. src/server.jl
