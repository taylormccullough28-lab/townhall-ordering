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
| `index.html` — sign-in + a read-back of what RLS grants | Written, **not executed** |
| Board UI port | Not started — waiting on sign-in being proven |
| Admin screen for the roster | Not started |

**Nothing in `data.js` has been run.** The environment it was written in cannot
reach Supabase, and sign-in needs a real browser session, so every line of it is
unexercised. Expect the first run to surface mistakes; the schema and the relay
underneath it are the parts that have actually been tested.

## Deploying

Vercel, **Root Directory `preshift-app`**, Framework Preset Other. No build step.

Two settings that will otherwise waste an afternoon:

- **Vercel Authentication must be OFF** for this project. Managers are not
  members of the Vercel team; with it on they hit a login wall they cannot pass.
  This is the opposite of what the ordering prototype wants.
- **Supabase → Authentication → URL Configuration** needs the deployed origin in
  both Site URL and Redirect URLs, or the magic link will refuse to complete.

Supabase's built-in email sender is rate limited to a handful per hour on a free
project. That is enough to test with and not enough to roll out on; a real SMTP
sender is a later step, not a blocker now.

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
