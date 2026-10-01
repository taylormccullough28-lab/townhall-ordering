# Pre-shift board — v1 app

Static files. No build step, no bundler: `index.html` loads `supabase-js` from a
CDN and imports `data.js` as a module. Deploys to any static host; the target is
Vercel.

## Status

| Piece | State |
|---|---|
| Schema, roster, RLS | Done, verified by simulating roles |
| Board merge RPCs, realtime publication | Done, deep merge verified |
| `data.js` — auth, boards, 86 list, names, posting | Written, **not executed** |
| `index.html` — sign-in screen and board UI | Not started |
| Admin screen for the roster | Not started |

**Nothing in `data.js` has been run.** The environment it was written in cannot
reach Supabase, and sign-in needs a real browser session, so every line of it is
unexercised. Expect the first run to surface mistakes; the schema and the relay
underneath it are the parts that have actually been tested.

## What replaces what

The prototype was a Claude artifact using two runtime capabilities. Neither
exists outside that host, which is the whole reason for this rebuild:

| Prototype | Here |
|---|---|
| `claude.use("db")` | Supabase Postgres, `boards` + `eighty_six` |
| `.onSnapshot(...)` | `postgres_changes` channels |
| `claude.use("user")`, `user.profiles()` | Supabase Auth + the `managers` roster |
| Copy to clipboard | `post.send()` through the relay, clipboard kept as fallback |

`data.js` is a real API rather than a shim imitating the artifact one — a fake
Firestore-ish surface over Supabase would read as a mystery to whoever picks
this up.

## Access

`data.js` enforces nothing. Every table has RLS on, and the policies in
migration 0003 decide what a signed-in manager can see. A missing check in this
file is a bug, not a security hole. The publishable key in the source is public
by design: it names the project, it does not authorise anything.

## Sign-in

Magic link to the email on the manager's roster row. First sign-in binds the
auth user to that row, scoped to the unbound row matching that exact address so
it cannot claim someone else's. An address that is not on the roster, or whose
row is inactive, both resolves to no manager here and sees nothing through RLS.
