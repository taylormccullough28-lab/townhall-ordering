// Relay for the pre-shift board's "Post to GroupMe" button.
//
// Why this exists: a GroupMe bot_id is a bearer credential. Anyone holding it
// can post to the group forever, with no further auth. The board is a page the
// browser downloads, so a bot_id placed there is readable by every manager who
// opens it and by anyone they forward the link to. It lives here instead, in
// this function's environment, and never reaches the client.

const MAX_CHARS = 900;            // conservative; GroupMe's real cap is ~1000, unconfirmed
const RATE_WINDOW_MS = 60_000;
const RATE_MAX = 6;               // posts per warm instance per minute

let recent = [];

function splitMessage(text, limit) {
  const out = [];
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

export default async function handler(req, res) {
  const origin = req.headers.origin || "";
  // Set on the Vercel project once we know the artifact's real origin from the
  // first test. Empty means "allow any origin" - acceptable only while testing
  // against a throwaway group.
  const allowList = (process.env.ALLOWED_ORIGINS || "")
    .split(",").map(s => s.trim()).filter(Boolean);
  const originOk = allowList.length === 0 || allowList.includes(origin);

  res.setHeader("Access-Control-Allow-Origin", allowList.length === 0 ? "*" : origin);
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "content-type");
  res.setHeader("Vary", "Origin");

  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  if (!originOk) return res.status(403).json({ error: "origin not allowed", sawOrigin: origin });

  const body = typeof req.body === "string" ? safeParse(req.body) : (req.body || {});
  const text = typeof body.text === "string" ? body.text.trim() : "";

  // Lets us confirm the endpoint is alive and see what origin the board sends,
  // without putting anything in anyone's GroupMe.
  if (body.dryRun) {
    return res.status(200).json({
      ok: true, dryRun: true, sawOrigin: origin || "(none sent)",
      botIdConfigured: Boolean(process.env.GROUPME_BOT_ID),
      wouldSend: text ? splitMessage(text, MAX_CHARS).length : 0,
    });
  }

  if (!text) return res.status(400).json({ error: "text required" });

  const botId = process.env.GROUPME_BOT_ID;
  if (!botId) return res.status(500).json({ error: "GROUPME_BOT_ID is not set on this project" });

  const now = Date.now();
  recent = recent.filter(t => now - t < RATE_WINDOW_MS);
  if (recent.length >= RATE_MAX) {
    return res.status(429).json({ error: "rate limited", retryAfterMs: RATE_WINDOW_MS });
  }
  recent.push(now);

  const chunks = splitMessage(text, MAX_CHARS);
  const sent = [];
  for (const [i, chunk] of chunks.entries()) {
    const label = chunks.length > 1 ? `(${i + 1}/${chunks.length})\n${chunk}` : chunk;
    let r;
    try {
      r = await fetch("https://api.groupme.com/v3/bots/post", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bot_id: botId, text: label }),
      });
    } catch (e) {
      return res.status(502).json({ error: "could not reach GroupMe", detail: String(e), sent });
    }
    if (!r.ok) {
      return res.status(502).json({
        error: "GroupMe rejected the post", groupmeStatus: r.status,
        groupmeBody: (await r.text()).slice(0, 300), sentBefore: sent.length,
      });
    }
    sent.push(i + 1);
  }
  return res.status(200).json({ ok: true, messages: sent.length });
}

function safeParse(s) { try { return JSON.parse(s); } catch { return {}; } }
