// Relay for the pre-shift board's "Post to GroupMe" button.
//
// A GroupMe bot_id is a bearer token: anyone holding it can post to that group
// indefinitely, with no further authentication. The board is a page the browser
// downloads, so a bot_id placed in it is readable by every manager who opens the
// board and by anyone they forward the link to. It lives in the preshift_bots
// table instead, which has RLS on and no policies - unreachable from any client.
// Only the service role key, injected here and never sent to a browser, reads it.
//
// A successful post also logs a completion row and texts Taylor. The trigger is
// server-side on purpose: a client cannot fabricate a completion it did not send.
//
// verify_jwt is DISABLED, and the key check lives in this file instead. With
// gateway JWT verification on, a browser's CORS preflight OPTIONS - which by
// specification carries no credentials - is rejected with 401 before reaching
// this code, and the browser reports it as a CORS failure. The check below is
// the same strength as what the gateway gave us, because the key it accepts is
// publishable by design. It keeps unkeyed scanners out; it is not real
// authorization. Real gating needs the app logins.

import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const GROUPME_ENDPOINT = "https://api.groupme.com/v3/bots/post";
const MAX_CHARS = 900;        // conservative; GroupMe's real cap is reported near 1000
const RATE_WINDOW_MS = 60_000;
const RATE_MAX = 6;           // per warm instance, not a global quota

// Publishable keys for this project. Public by design - they appear in the app.
const ACCEPTED_KEYS = new Set([
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1iYm56enZxa2NxamZob253YWxiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY5ODgxMTQsImV4cCI6MjEwMjU2NDExNH0.mSqHRHRC-ytpH7XHNoHYvcWSVQ1n0QX2WDOVwCJss5M",
  "sb_publishable_GyeS8YntNpZE2npl7vaVrw_O1COcRYL",
]);

const SB_URL = Deno.env.get("SUPABASE_URL");
const SB_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

let recent: number[] = [];

const CORS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Max-Age": "86400",
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}

function presentedKey(req: Request): string | null {
  const apikey = req.headers.get("apikey");
  if (apikey) return apikey;
  const auth = req.headers.get("authorization") ?? "";
  const m = auth.match(/^Bearer\s+(.+)$/i);
  return m ? m[1].trim() : null;
}

function sbHeaders(extra: Record<string, string> = {}): Record<string, string> {
  return {
    apikey: SB_KEY ?? "",
    Authorization: `Bearer ${SB_KEY ?? ""}`,
    "Content-Type": "application/json",
    ...extra,
  };
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
  if (!SB_URL || !SB_KEY) return null;
  const url = `${SB_URL}/rest/v1/preshift_bots?store=eq.${encodeURIComponent(store)}&select=bot_id`;
  const r = await fetch(url, { headers: sbHeaders() });
  if (!r.ok) return null;
  const rows = await r.json();
  return Array.isArray(rows) && rows[0]?.bot_id ? String(rows[0].bot_id) : null;
}

async function logPost(store: string, chars: number, parts: number): Promise<number | null> {
  if (!SB_URL || !SB_KEY) return null;
  const r = await fetch(`${SB_URL}/rest/v1/post_log`, {
    method: "POST",
    headers: sbHeaders({ Prefer: "return=representation" }),
    body: JSON.stringify({ store, chars, parts }),
  });
  if (!r.ok) return null;
  const rows = await r.json();
  return Array.isArray(rows) && rows[0]?.id ? Number(rows[0].id) : null;
}

async function markNotified(id: number, ok: boolean, err: string | null): Promise<void> {
  if (!SB_URL || !SB_KEY) return;
  await fetch(`${SB_URL}/rest/v1/post_log?id=eq.${id}`, {
    method: "PATCH",
    headers: sbHeaders(),
    body: JSON.stringify({ notified: ok, notify_error: err }),
  }).catch(() => {});
}

interface SmsConfig {
  account_sid: string | null;
  auth_token: string | null;
  from_number: string | null;
  to_number: string | null;
  enabled: boolean;
}

async function smsConfig(): Promise<SmsConfig | null> {
  if (!SB_URL || !SB_KEY) return null;
  const r = await fetch(`${SB_URL}/rest/v1/sms_config?id=eq.1&select=*`, { headers: sbHeaders() });
  if (!r.ok) return null;
  const rows = await r.json();
  return Array.isArray(rows) && rows[0] ? rows[0] as SmsConfig : null;
}

// Returns null on success, otherwise a short reason. Never throws to the caller:
// the GroupMe post has already gone out by this point, and a failed text must not
// make the manager think the post failed.
async function sendCompletionText(store: string, parts: number): Promise<string | null> {
  const c = await smsConfig();
  if (!c) return "sms_config unreadable";
  if (!c.enabled) return "sms not enabled yet";
  if (!c.account_sid || !c.auth_token || !c.from_number || !c.to_number) {
    return "sms credentials incomplete";
  }
  const suffix = parts > 1 ? ` (${parts} parts)` : "";
  const body = new URLSearchParams({
    From: c.from_number,
    To: c.to_number,
    Body: `Pre-shift board posted for ${store}${suffix}.`,
  });
  const r = await fetch(
    `https://api.twilio.com/2010-04-01/Accounts/${encodeURIComponent(c.account_sid)}/Messages.json`,
    {
      method: "POST",
      headers: {
        Authorization: "Basic " + btoa(`${c.account_sid}:${c.auth_token}`),
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body,
    },
  );
  if (!r.ok) return `twilio ${r.status}: ${(await r.text()).slice(0, 200)}`;
  return null;
}

Deno.serve(async (req: Request) => {
  // Preflight first, before any auth check. A browser preflight carries no
  // credentials; rejecting it is what breaks a browser caller.
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  const key = presentedKey(req);
  if (!key || !ACCEPTED_KEYS.has(key)) {
    return json({ error: "missing or unrecognised project key" }, 401);
  }

  let body: Record<string, unknown> = {};
  try { body = await req.json(); } catch { /* treated as empty below */ }

  const store = typeof body.store === "string" && body.store ? body.store : "test";
  const text = typeof body.text === "string" ? body.text.trim() : "";
  const origin = req.headers.get("origin") ?? "(none sent)";

  // Confirms the function is live, the bot row is readable, whether the text is
  // wired up, and what Origin the caller sends - without putting anything in
  // anyone's GroupMe or sending a text.
  if (body.dryRun) {
    const id = await botIdFor(store);
    const c = await smsConfig();
    return json({
      ok: true,
      dryRun: true,
      store,
      sawOrigin: origin,
      botConfigured: Boolean(id),
      smsEnabled: Boolean(c?.enabled),
      smsCredentialsPresent: Boolean(c?.account_sid && c?.auth_token && c?.from_number && c?.to_number),
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

  // The post is out. Everything below is best-effort and cannot fail the result.
  const logId = await logPost(store, text.length, sent).catch(() => null);
  let notifyError: string | null = "not attempted";
  try {
    notifyError = await sendCompletionText(store, sent);
  } catch (e) {
    notifyError = String(e).slice(0, 200);
  }
  if (logId !== null) await markNotified(logId, notifyError === null, notifyError);

  return json({
    ok: true,
    messages: sent,
    store,
    logged: logId !== null,
    notified: notifyError === null,
    notifyNote: notifyError,
  });
});
