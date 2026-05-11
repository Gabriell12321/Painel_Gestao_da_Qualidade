// deno-lint-ignore-file
// @ts-nocheck
// Deno Tools microservice: URL encode/decode
// Permissions: --allow-env --allow-net

const hostname = Deno.env.get("DENO_TOOLS_HOST") ?? "0.0.0.0";
const port = Number(Deno.env.get("DENO_TOOLS_PORT") ?? "8092");

function json(body: unknown, init: ResponseInit = {}): Response {
  const base = { headers: { "content-type": "application/json" } };
  return new Response(JSON.stringify(body), { ...base, ...init });
}

Deno.serve({ hostname, port }, async (req: Request) => {
  try {
    const url = new URL(req.url);
    if (req.method === "GET" && url.pathname === "/health") {
      return json({ ok: true });
    }
    if (req.method === "POST" && url.pathname === "/url/encode") {
      const text = await req.text();
      return json({ ok: true, data: encodeURIComponent(text) });
    }
    if (req.method === "POST" && url.pathname === "/url/decode") {
      const text = await req.text();
      try {
        const out = decodeURIComponent(text);
        return json({ ok: true, data: out });
      } catch (_) {
        return json({ ok: false, error: "invalid percent encoding" }, { status: 400 });
      }
    }
    return new Response(null, { status: 404 });
  } catch (e) {
    return json({ ok: false, error: String(e) }, { status: 500 });
  }
});

// Log server address for convenience
console.log(`Deno Tools running on http://${hostname}:${port}`);
