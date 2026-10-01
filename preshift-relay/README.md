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

## What a successful post does

1. Splits the text if needed and posts each part to GroupMe.
2. Writes a row to `post_log` — store, timestamp, length, parts. This is the
   completion history; it is written server-side so a client cannot fabricate a
   completion it never sent.
3. Texts Taylor, if `sms_config.enabled` is set.

Steps 2 and 3 are best-effort and cannot fail the response. By the time they
run the post has already gone out, and a failed text must not make a manager
think the post failed. The reason a text did not send is recorded in
`post_log.notify_error` rather than thrown away.

## The completion text

A Twilio **toll-free** number, not a 10-digit one. A 10-digit number sending
application traffic to US phones requires A2P 10DLC brand and campaign
registration, and since 2026-06-30 a privacy policy URL and a terms URL on
every campaign — disproportionate for texting one person. Toll-free needs only
a verification review, about three business days, and costs roughly $2.15/month
plus well under a dollar of messages at two shifts a day.

Credentials go in `sms_config` through the Supabase dashboard, never through a
chat window. Set `enabled = true` once the number is verified; no redeploy is
needed.

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

- dry run → `{"ok":true,"botConfigured":true,"smsEnabled":false,"smsCredentialsPresent":false}`
- live post → `{"ok":true,"messages":1,"logged":true,"notified":false,"notifyNote":"sms not enabled yet"}`
- the resulting `post_log` row recorded `notified=false` with that reason, and
  the post still returned success

The Twilio leg itself is unexercised — there is no account or verified number
yet.

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
