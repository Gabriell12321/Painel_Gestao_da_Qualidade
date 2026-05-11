import jester
import json
import os
import std/random
import std/strutils
import std/sha1
import times

randomize()

proc genToken*(len: int = 32): string =
  let chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
  for i in 0 ..< len:
    result.add(chars[rand(chars.len - 1)])

proc genUUIDv4*(): string =
  # Simple UUIDv4-like generator (not cryptographically strong)
  # Format: 8-4-4-4-12
  let hexchars = "0123456789abcdef"
  var s: seq[char] = @[]
  for i in 0 ..< 32:
    s.add(hexchars[rand(15)])
  s.insert('-', 8)
  s.insert('-', 13)
  s.insert('-', 18)
  s.insert('-', 23)
  return s.join("")

settings:
  port = parseInt(getEnv("NIM_TOOLS_PORT", "8087"))
  bindAddr = getEnv("NIM_TOOLS_HOST", "0.0.0.0")

routes:
  get "/health":
    resp $(%*{"ok": true})

  get "/uuid":
    resp $(%*{"ok": true, "uuid": genUUIDv4()})

  get "/token":
    let size = try: parseInt(request.queryParams.getOrDefault("size", "32")) except: 32
    resp $(%*{"ok": true, "token": genToken(size)})
