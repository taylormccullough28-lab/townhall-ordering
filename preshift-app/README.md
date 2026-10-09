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
| `index.html` — the board, with the sign-in gate | In use |
| `check.html` — diagnostic: what the database says about your sign-in | In use |
| `admin.html` — the roster | Written, **not executed**; its RLS verified |
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

## The port

`index.html` is the prototype with its data layer swapped, not a rewrite. The UI,
CSS, post builder and section rendering are the proven ones. Every write in the
prototype funnelled through a single `patchShift`, and only five places touched
the data layer at all, so the port is six patch points:

| Prototype | Now |
|---|---|
| `patchShift` → `db.doc().set/update` | `boards.ensure` then `patchContent`, with `coach` split to `patchCoaching` |
| `db.doc().onSnapshot` | one load, then a `postgres_changes` channel on that row |
| `db.doc().get()` for carry-forward | `boards.load` of the previous shift |
| `user.profiles()` | `people.names()` against the roster |
| `db.doc("config/stores").set` | removed — stores are admin-only now, and the board no longer edits them |
| artifact capability boot | magic-link gate, roster lookup, store list |

### The 86 list is still in `content`

Migration 0003 gives the 86 list its own table and the app does not use it yet.
The UI patches the whole `eightySix` array in one write, so moving it to per-row
inserts means changing six more call sites in code that cannot be run here. A
working board first. The table stays because the reasoning for it holds — a real
timestamp per item is what the "86 items added mid-shift" measure needs — and
moving to it is the next migration once the board can actually be exercised.

### The roster screen

`admin.html`. One screen, whole roster visible, one tap to remove — which is what
the PRD asks for, because the cost of forgetting to revoke a departed manager is
worse than the cost of a mistaken tap, and the same button undoes it.

Rows are deactivated, never deleted: the row keeps the attribution on every 86
and Yes/No that person recorded. It shows three states rather than two — active,
removed, and **never signed in**, which is the one worth seeing when someone says
the link did not work.

Access is the database's decision, not the page's. Verified by simulating both
roles against the real policies:

| Acting as | Roster rows visible | Could deactivate someone | Could add someone |
|---|---|---|---|
| Ordinary manager | 1 — only themselves | no, 0 rows affected | no |
| Admin | 2 — everyone | yes | yes |

So a non-admin who opens this page anyway reads nothing and writes nothing. The
hidden buttons are a courtesy; the policies are the control.

### Known gaps

- **Posting will fail for `townhall-columbus`** until a bot row exists for it.
  `preshift_bots` only has the `test` row. The error surfaces on the button.
- **`readOnly` is never set.** The prototype derived it from a capability check.
  Here every active roster manager can write their own store, and a refused
  write would surface as a failed save rather than a disabled field.
- **A board created by another manager mid-session is not subscribed to** until
  this view writes or reloads, because the channel attaches to a row id that did
  not exist at load.

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
