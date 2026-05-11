require "kemal"
require "digest/sha256"

host = ENV["CRYSTAL_TOOLS_HOST"]? || "0.0.0.0"
port = (ENV["CRYSTAL_TOOLS_PORT"]? || "8091").to_i

get "/health" do
  {ok: true}.to_json
end

post "/sha256" do |env|
  body = env.request.body.try &.gets_to_end || ""
  digest = Digest::SHA256.hexdigest(body)
  {ok: true, sha256: digest}.to_json
end

Kemal.config.host_binding = host
Kemal.config.port = port
Kemal.run
