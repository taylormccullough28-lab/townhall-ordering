// Relay for the pre-shift board's "Post to GroupMe" button.
//
// A GroupMe bot_id is a bearer token: anyone holding it can post to that group
// indefinitely, with no further authentication. The board is a page the browser
// downloads, so a bot_id placed in it is readable by every manager who opens the
// board and by anyone they forward the link to. It lives in the preshift_bots
// table instead, which has RLS on and no policies - unreachable from any client.
// Only the service role key, injected into this function's environment and never
// sent to a browser, can read it.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const GROUPME_ENDPOINT = "https://api.groupme.com/v3/bots/post";
const MAX_CHARS = 900;        // conservative; GroupMe's real cap is reported near 1000
const RATE_WINDOW_MS = 60_000;
const RATE_MAX = 6;           // per warm instance, not a global quota

let recent: number[] = [];

const CORS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}

// Split on line boundaries so a post never breaks mid-sentence. A single
// over-long line is hard-split rather than dropped.
function splitMessage(text: string, limit: number): string[] {
  const out: string[] = [];
  let buf = "";
  for (const line of text.split("\n")) {
    if (line.length > limit) {
      if (buf) { out.push(buf); buf = ""; }
      for (let i = 0; i < line.length; i += limit) out.push(line.slice(i, i + limit));
      continue;
    }
    if ((buf ? buf.length + 1 : 0) + line.length > limit) { out.push(buf); buf = line; }
    else buf = buf ? buf + "\n" + line : line;
  }
  if (buf) out.push(buf);
  return out;
}

async function botIdFor(store: string): Promise<string | null> {
  const base = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!base || !key) return null;
  const url = `${base}/rest/v1/preshift_bots?store=eq.${encodeURIComponent(store)}&select=bot_id`;
  const r = await fetch(url, { headers: { apikey: key, Authorization: `Bearer ${key}` } });
  if (!r.ok) return null;
  const rows = await r.json();
  return Array.isArray(rows) && rows[0]?.bot_id ? String(rows[0].bot_id) : null;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  let body: Record<string, unknown> = {};
  try { body = await req.json(); } catch { /* treated as empty below */ }

  const store = typeof body.store === "string" && body.store ? body.store : "test";
  const text = typeof body.text === "string" ? body.text.trim() : "";
  const origin = req.headers.get("origin") ?? "(none sent)";

  // Confirms the function is live, the bot row is readable, and what Origin the
  // caller sends - without putting anything in anyone's GroupMe.
  if (body.dryRun) {
    const id = await botIdFor(store);
    return json({
      ok: true,
      dryRun: true,
      store,
      sawOrigin: origin,
      botConfigured: Boolean(id),
      wouldSend: text ? splitMessage(text, MAX_CHARS).length : 0,
    });
  }

  if (!text) return json({ error: "text required" }, 400);

  const now = Date.now();
  recent = recent.filter((t) => now - t < RATE_WINDOW_MS);
  if (recent.length >= RATE_MAX) {
    return json({ error: "rate limited", retryAfterMs: RATE_WINDOW_MS }, 429);
  }
  recent.push(now);

  const botId = await botIdFor(store);
  if (!botId) return json({ error: `no bot configured for store "${store}"` }, 404);

  const chunks = splitMessage(text, MAX_CHARS);
  let sent = 0;
  for (const [i, chunk] of chunks.entries()) {
    const payload = chunks.length > 1 ? `(${i + 1}/${chunks.length})\n${chunk}` : chunk;
    let r: Response;
    try {
      r = await fetch(GROUPME_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bot_id: botId, text: payload }),
      });
    } catch (e) {
      return json({ error: "could not reach GroupMe", detail: String(e), sent }, 502);
    }
    if (!r.ok) {
      return json({
        error: "GroupMe rejected the post",
        groupmeStatus: r.status,
        groupmeBody: (await r.text()).slice(0, 300),
        sent,
      }, 502);
    }
    sent++;
  }
  return json({ ok: true, messages: sent, store });
});
