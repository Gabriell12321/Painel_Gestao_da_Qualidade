module main

import vweb
import os

struct App {
    vweb.Context
}

fn main() {
    host := os.getenv_opt('V_TOOLS_HOST') or { '0.0.0.0' }
    port := (os.getenv_opt('V_TOOLS_PORT') or { '8088' }).int()
    vweb.run(&App{}, port: port, host: host) or { panic(err) }
}

@['/health']
pub fn (mut app App) health() vweb.Result {
    return app.json({ 'ok': true })
}

fn slugify(s string) string {
    mut out := []rune{}
    for r in s.runes() {
        if r.is_letter() || r.is_digit() {
            out << r.to_lower()
        } else if r == ` ` || r == `-` || r == `_` {
            out << `-`
        }
    }
    // collapse multiple dashes
    mut res := ''
    mut prev_dash := false
    for ch in out {
        if ch == `-` {
            if !prev_dash { res += '-' }
            prev_dash = true
        } else {
            res += ch.ascii_str()
            prev_dash = false
        }
    }
    return res.trim('-')
}

@['/slug'; get]
pub fn (mut app App) slug() vweb.Result {
    text := app.query['text'] or { '' }
    if text.len == 0 {
        return app.json({ 'ok': false, 'message': 'missing text' })
    }
    s := slugify(text)
    return app.json({ 'ok': true, 'slug': s })
}
