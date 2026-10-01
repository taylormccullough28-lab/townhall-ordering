# Pre-shift GroupMe relay

One serverless function. The pre-shift board calls it; it forwards the text to a
store's GroupMe group.

It exists because a GroupMe `bot_id` is a bearer credential — anyone holding it
can post to the group indefinitely, with no further authentication. The board is
a page the browser downloads, so a `bot_id` placed in it is readable by every
manager who opens the board, and by anyone they forward the link to. Keeping it
in this function's environment is the whole point.

## Deploying

This folder is the Vercel project root (set **Root Directory** to
`preshift-relay`), so nothing else in this repository is served.

## Environment variables

| Name | Required | Notes |
|---|---|---|
| `GROUPME_BOT_ID` | yes | Set it in the Vercel dashboard. Never commit it, and don't paste it into a chat. |
| `ALLOWED_ORIGINS` | no | Comma-separated. Empty means any origin is accepted — only acceptable while testing against a throwaway group. Set it once the board's real origin is known. |

## Checking it without posting

`POST` with `{"dryRun": true}` reports whether the bot id is configured and
echoes back the `Origin` it saw, without sending anything to GroupMe.

## Known limits

- The rate limit is in-memory, so it is per warm instance rather than global. It
  blunts a runaway loop; it is not a real quota.
- Messages are split at 900 characters. GroupMe's actual cap is reported to be
  around 1000 but is not confirmed against the API.
- There is no caller authentication. Anyone with this URL can post to the group.
  Revocability is what it buys you over an exposed `bot_id`: the endpoint can be
  deleted or rotated without touching GroupMe.
