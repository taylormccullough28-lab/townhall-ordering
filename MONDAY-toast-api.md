# Monday: Toast API access — what to capture

Toast API access expected Monday. The `ToastApiSource` adapter (`thbev/sources/toast_api.py`) refuses to run today and enumerates nine unknowns. This is the list to close, in priority order, so one session answers all of it.

---

## 1. Which APIs were granted? (answer this first — it changes everything below)

Toast exposes several APIs and reporting is not the same thing as the transactional API. Confirm exactly which are enabled for the Short North restaurant GUID:

- [ ] **Orders API** — order → check → selection → **modifier** detail
- [ ] **Menus / Config API** — menu, menu group, item structure
- [ ] **Labor, Restaurants, Partners** — not needed for this, but note what's on
- [ ] Any **reporting or analytics** endpoint, and whether PMIX is reachable that way at all

**Why this is first:** if the **Orders API** is granted, it likely supersedes the entire export plan. It returns the raw selections that `ItemSelectionDetails` is derived from — *including modifiers*. That would resolve the single biggest hole in the project (no modifier data anywhere, every spirit defaulting to a 1.5oz single) without needing a modifier report at all. Verify before assuming.

Conversely: API access does **not** automatically mean PMIX is available. PMIX is a report. Do not assume the report and the API return the same shape.

## 2. Credentials and connection

- [ ] Auth model — client credentials, token lifetime, refresh mechanics
- [ ] Base host — production vs. sandbox
- [ ] **Restaurant GUID for TownHall Short North specifically** (the account has ~11 units; the wrong GUID silently returns another restaurant's data)
- [ ] Rate limits and pagination model
- [ ] Whether historical backfill is available, and how far back

**Do not paste credentials into a chat.** Store them as environment variables or in a secrets manager. The adapter reads config, never literals.

## 3. Data semantics — the ones that silently corrupt numbers

- [ ] **Timestamps: UTC or local?** Everything in this system buckets on a 4:00 AM business-day boundary. A UTC timestamp misfiled by four hours moves late-night sales into the wrong day, which is most of the weekend volume.
- [ ] **Does the API expose Toast's business date**, or only wall-clock time? If it gives business date directly, use it and stop deriving.
- [ ] **How are voids represented?** A flag, a status, a negative quantity, or absence.
- [ ] **How are comps represented?** They must count as depletion but stay distinguishable from paid sales.
- [ ] **Modifier structure** — are pour modifiers (Single / Rocks / Double) their own selections, child selections, or an attribute? This determines the join and whether double-counting is possible.
- [ ] **Sales Category** — present per selection? What are the actual values at Short North? Everything observed so far came from FWD and TownHall CLE and is not authoritative.

## 4. Capture for the record

- [ ] One full **raw JSON response** for a single busy business day, saved to `/data/` (gitignored). This becomes the real test fixture, replacing the synthetic ones.
- [ ] The complete list of distinct **Sales Category**, **Menu**, and **Menu Group** values at Short North. The mapping table is a skeleton until this exists.

---

## Do not wait for Monday

Two things matter more than the API and are answerable now:

1. **Which order guide is current** — `TH_ORDER_GUIDE.docx` or `TownHall Order Guide 2026.xlsx`. They disagree on order days, delivery days and rep names for Heidelberg, Columbus Distributing, Superior and Sixth City, and the xlsx lists five vendors the other omits. The scheduling engine is built on the docx and the published quick-reference guide is too. If the xlsx is current, both are wrong right now.
2. **The MarginEdge decision** — see `FINDINGS-marginedge.md`. MarginEdge already has the Toast feed running daily. If its API is the better source, Toast API access matters less than it looks, and the adapter to build is `MarginEdgeApiSource` rather than `ToastApiSource`. Worth resolving before Monday so the session targets the right system.
