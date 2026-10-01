# Pre-shift GroupMe relay

One edge function. The pre-shift board calls it; it forwards the text to a
store's GroupMe group.

It exists because a GroupMe `bot_id` is a bearer credential — anyone holding it
can post to the group indefinitely, with no further authentication. The board is
a page the browser downloads, so a `bot_id` placed in it is readable by every
manager who opens the board, and by anyone they forward the link to. Keeping it
server-side is the whole point.

## Where it runs

Supabase project `supabase-coral-button` (`mbbnzzvqkcqjfhonwalb`), function
`preshift-post`:

```
https://mbbnzzvqkcqjfhonwalb.supabase.co/functions/v1/preshift-post
```

`verify_jwt` is on, so callers send the project's publishable key. That key is
designed to live in client code; the `bot_id` is not, and does not.

An earlier Vercel implementation was removed in favour of this one rather than
kept alongside it — two relays would drift.

## Where the bot id lives

The `preshift_bots` table, one row per store, with RLS on and no policies. No
browser can read it. The function reads it with the service role key, which
Supabase injects into the function environment.

Adding a store's bot is a SQL insert, not a code change:

```sql
insert into public.preshift_bots (store, bot_id, label)
values ('townhall-columbus', '<bot id from dev.groupme.com/bots>', 'TownHall Columbus staff');
```

## Checking it without posting

```json
{ "dryRun": true, "store": "test" }
```

Reports whether the bot row is readable and echoes the `Origin` it saw. Sends
nothing to GroupMe.

## Verified behaviour

Both exercised against the test group on 2026-10-01, via `pg_net` from SQL:

- dry run → `{"ok":true,"botConfigured":true,"wouldSend":1}`
- live post → `{"ok":true,"messages":1}`, accepted by GroupMe

## Limits, stated plainly

- **No caller authentication beyond the publishable key**, which is public by
  design. Anyone with the board can post to that store's group. What this buys
  over an exposed `bot_id` is revocability and scope: the function can be
  deleted or the row rotated without touching GroupMe, and the credential itself
  never leaves the server. Real gating needs the app's logins.
- **The rate limit is in-memory**, so per warm instance, not a global quota. It
  blunts a runaway loop.
- **Messages split at 900 characters.** GroupMe's real cap is reported near 1000
  but is not confirmed against their docs, which were unreachable from the build
  environment.
- **`Access-Control-Allow-Origin` is `*`.** The board's sandboxed origin was not
  determinable ahead of the first browser call; tighten this once a real click
  reports it.
