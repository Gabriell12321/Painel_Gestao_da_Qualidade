version       = "0.1.0"
author        = "IPPEL"
description   = "Nim tools microservice (UUID and random token)"
license       = "MIT"
srcDir        = "src"
bin           = @["nim_tools"]
requires      = @[
  "nim >= 1.6.0",
  "jester >= 0.5.0"
]
