# Findings: MarginEdge is already live — implications for the beverage ordering PRD

**Date:** 2026-08-29 · **Status:** Research findings, pending decisions
**Method:** Search of company Outlook and SharePoint/OneDrive (tenant `corpmg`), plus public documentation research.

---

## Headline

MarginEdge is an **active, daily-traffic system at TownHall Columbus**, and the **Toast POS feed is already connected**. This is not a procurement question — it is already paid for and running. It changes the answer to two of the PRD's open questions and makes part of the P0 scope redundant.

---

## Confidence levels — read this first

Findings fall into three tiers, and they should not be treated equally:

| Tier | What it covers | Confidence |
|---|---|---|
| **A. Directly observed** | Everything in "What exists today" below — read firsthand from Outlook and SharePoint, quoted verbatim | High |
| **B. Publicly documented** | MarginEdge feature names and behavior in "What MarginEdge does" | Moderate — see caveat |
| **C. Inference** | That TownHall Columbus's order guides already hold priced vendor SKUs | Unverified — one login confirms or kills it |

**Caveat on tier B:** all three MarginEdge domains (`marginedge.com`, `help.marginedge.com`, `developer.marginedge.com`) are blocked by this environment's egress proxy. Tier B comes from *search-result summaries of those pages, not the pages themselves*. Feature names are consistently attested across independent results, so the features exist. **API resource coverage, auth scheme, endpoints and field names are NOT verified and no one should build against them until someone opens the developer portal directly.**

---

## What exists today (directly observed)

### The Toast feed is already running
From `[MarginEdge] Nightly Sales report for 08/29/2026`, TownHall - Columbus block:

```
TownHall - Columbus | Week of 08/24/2026
        This Week   Last Week   %      Last Year   %
Mon     $13,192     $13,580     -3 %   $16,833     -22 %
Tue     $12,162     $17,980     -32 %  $14,615     -17 %
Wed     $11,758     $22,782     -48 %  $14,373     -18 %
Thu     $32,120     $49,159     -35 %  $36,952     -13 %
Fri     $21,907     $33,735     -35 %  $89,162     -75 %
Sun     $23,540     $45,340
POS Sales updated through 08/28/2026
```

The last line is the important one. **Toast sales for Short North flow into MarginEdge automatically, daily.** The PRD's entire manual-export plan — the PMIX vs. ItemSelectionDetails question, the "will Toast attach a file or render it inline" problem, Open Question 4 — is solved upstream by a system already in the building.

Note also: **Sunday does ~$23K.** That is the business happening after the Sunday 5–7pm order cutoffs, and it is why the post-cutoff depletion adjustment matters.

### Beverage invoices are flowing
- TownHall Columbus intake address: **`townhallcolumbus@meinvoices.com`**
- Three **Arena Liquor** invoices for TownHall Columbus visible in August alone (`OH0002847733`, `OH0002839045`, `OH0002830416`) — sequential numbering, so this is routine.
- Org-wide: **437 invoices processed** in the week of Aug 17–23.

### The inventory module is not being used
From the Weekly Snapshot, Aug 17–23: **`Inventories Closed: 0`** across all EHG restaurants. The capability exists and is unconfigured — a configuration gap, not a capability gap.

### The org has already run this process elsewhere
`Wave Inventory Procedures.docx` documents a weekly beverage count run *inside MarginEdge* at another property:
> "Inventory should be counted by each Sunday and closed on Mondays (am preferred). Count and record all beer, wine, liquor, and non-alcoholic products on the printed count sheets."

So the workflow is known to the org. It just isn't running at Short North.

### An operational collision worth knowing about
From `Operator_SOP_Ramp_MarginEdge.docx`:
> "**DEADLINE: All receipts/invoices must be uploaded to Margin Edge and all Ramp credit card transactions must be coded by 4:00 PM every Sunday.**"

That is the same shift and the same manager as the Sunday 5:00–7:00 PM order windows. Whatever this tool does on a Sunday is competing for that person's attention.

### No exports exist anywhere
Zero MarginEdge data exports in Outlook or SharePoint — no invoice detail, no product catalog, no vendor items, no usage. Every MarginEdge email is HTML-body or carries a *rejected invoice image*. Same situation as Toast: **the data exists in the system and has never been exported.**

---

## ⚠ Vendor order windows: two sources disagree

`ETHOS BEV PROGRAM/ETHOS ORDER GUIDES/TownHall Order Guide 2026.xlsx` (modified 2026-05-20, internally stamped "Updated 03.10.2025") contains a `CBUS VENDORS` sheet that **contradicts `TH_ORDER_GUIDE.docx`**, which is the source for both the PRD appendix and the published quick-reference guide.

| Vendor | Per `TH_ORDER_GUIDE.docx` (PRD + guide) | Per `TownHall Order Guide 2026.xlsx` |
|---|---|---|
| Heidelberg / Wine Trends | Wed 5pm → **Thu** · Tess Canby | **Mon 5pm → Tue** · **Chris Venci** |
| Columbus Distributing | Sun 7pm → **Mon** · Conner | **Sun 10pm → Tue, via BEES app** · **Chris McGlone** |
| Superior Beverage | Sun 7pm → **Mon** · Shane | Sun 7pm → **Tue**, Wed 7pm → Fri · **Jared** |
| Sixth City | Mon 5pm → **Tue** · Jenna Carelly | **Mon 4pm → Thu** · **Sarah** |
| Cavalier | Mon 5pm → Tue · Dan | **Mon 4pm** → Tue · Dan |
| Southern Glazer's | Mon 4pm → Tue · Bethany | Mon 4pm → Tue · Bethany ✓ |

Also in the XLSX and **absent from the PRD entirely**: Cutting Edge, Wolfs Ridge, Premium, Nocterra, Little Fish. And an ordering channel the PRD does not model — the **BEES app** for Columbus Distributing.

**One of these two sources is stale, and both are in active circulation.** This is a P0 correctness issue independent of everything else here: order windows and delivery days are the backbone of the scheduling engine, and the published quick-reference guide managers are using is built on one of them.

**Action required: confirm which source is current before the windows are encoded.**

### Also from that file
- **`CURRENT PAR` is empty for every beverage row.** Pars exist only for three CLE cigar lines. There are no pars to seed from.
- **No unit prices anywhere.** Confirms the catalog gap.
- No weekly order archive exists for TownHall Columbus — though one *does* for FWD (10+ weekly order files). This confirms the PRD's problem statement: Short North orders leave no record.

---

## What MarginEdge does (publicly documented — tier B)

### Public API
- Called the **MarginEdge Public API**; docs at `developer.marginedge.com`.
- **Included in any subscription at no additional cost.** No partner agreement indicated.
- **A MarginEdge Admin generates the key.** Every unit is automatically enabled.
- **One-way: MarginEdge → external.** It cannot read from external systems.
- Documented bulk exports: **orders, products, vendor items, usage, recipes, recipe ingredients, recipe cost histories.**

**Not verified, and deliberately not guessed at:** endpoint URLs, auth scheme, request/response shapes, rate limits, historical backfill — and critically, **whether invoices are exposed as a resource.** Invoices are conspicuously absent from the documented resource list. If invoice line items are not in the API, the receipts side of perpetual inventory gets harder and the recommendation below weakens.

### Theoretical On-Hand
> **Theoretical On Hand = Starting Inventory + Purchases − Sales − Waste**

Purchases from uploaded invoices; sales from the POS integration with PMIX mapping; waste from an optional log. **This is exactly the perpetual-inventory model in PRD Open Question 1(b), already built.**

Its documented limits match the PRD's own analysis: it needs an accurate starting count, on-hand is **not** auto-populated, and drift requires periodic recounts.

### Auto-generated order guides
> "For every one of your vendors who have invoices processed in MarginEdge, an Order Guide is automatically generated to include all available vendor items."

Pars settable per item, including **different values per day of week**. On-hand entered manually; the system calculates the quantity to return to par. Orders emailed to vendor addresses.

### Toast integration
Documented to provide sales import, labor, daily P&L and prime cost, **theoretical usage reports**, and accounting push. The PMIX→ingredient mapping the PRD calls "the heart of the system" is a named MarginEdge feature.

### Freepour
`marginedge.com/freepour` — a MarginEdge liquor-inventory product. Possibly relevant to the keg-level estimation problem. Not verified.

---

## Overlap analysis

### Already done by MarginEdge — rebuilding these is waste

| PRD item | Status |
|---|---|
| Product catalog (P0) | Auto-built from real invoices with actual SKUs, pack sizes, paid prices. The PRD's source is a Word doc with names only. |
| Toast sales ingest (P0) + ingest appendix | **Already running, automatically, daily.** |
| Invoice reconciliation (P1) | Core product. The EHG SOP already instructs marking discrepancies before upload. |
| Vendor price tracking (P2) | Every invoice is line-item priced. |
| Theoretical vs. actual variance (P1) | Named feature. **This is the Sculpture replacement.** |
| Per-vendor order output (P0) | Emails orders to vendor addresses — would cover the Arena email-only rule natively. |

### Genuinely not done by MarginEdge — this is the real product

1. **Event-driven forecasting.** MarginEdge orders to a static par. It has no concept of "next Saturday is an OSU home game, move light beer +90%." **This is the strongest justification for building anything.**
2. **Per-vendor order-window scheduling** with countdowns to six cutoffs across four days.
3. **Order-to-next-delivery** rather than order-to-par — the `days_of_cover` logic.
4. **Post-cutoff depletion adjustment.** Material at ~$23K of Sunday business.
5. **Keg return tracking and credit reconciliation.** Not a MarginEdge concept.
6. **Style-not-SKU recommendations** for rotating lines. MarginEdge's order guide is SKU-based by construction.
7. **Vendor routing rules** — OYO through Arena first.
8. **Reasoning line per quantity** — "sold 187, +60% OSU, 3 on hand, order 6" rather than par arithmetic.

---

## Recommendations

**1. Reframe this tool as a forecasting and scheduling layer on top of MarginEdge, not a standalone system.** The five-stage flow survives; stages 1 and 2 change where they get their inputs. The differentiated value is untouched.

**2. Replace the Toast manual-upload path with the MarginEdge Public API.** Resolves Open Question 4 outright. Keep the PMIX/ItemSelectionDetails parser as a documented fallback only.
*Precondition:* generate an API key as Admin and read `developer.marginedge.com` to confirm which resources are actually exposed — especially invoices.

**3. Source the product catalog from MarginEdge.** Real SKUs, pack sizes and paid prices already exist there. This also silently delivers the P2 price-tracking item.

**4. Demote to non-goals, delegating to MarginEdge:** invoice reconciliation, theoretical-vs-actual variance, vendor price tracking. **Keep the keg credit tracker** — MarginEdge does not do it.

**5. Rewrite Open Question 1 as a decision.** Recommended: short weekly count of order-critical items for V1, **with MarginEdge Theoretical On-Hand configured in parallel** so drift can be measured against real counts. Once the two agree within tolerance, drop to a monthly full count. Same conclusion the PRD reached, now with an already-paid-for implementation.

**6. New Phase 0 prerequisite: enable and configure the MarginEdge inventory and ordering modules for TownHall Columbus beverage.** `Inventories Closed: 0` says nobody is using them. A meaningful share of what the PRD scopes as *build* is actually *configuration of software already in the building*.

**7. Revisit the Sculpture replacement timeline.** If MarginEdge's variance reporting covers what Sculpture provided, that replacement is a configuration task achievable before a line of code ships. **That is the fastest available win and it should not wait on this build.**

---

## Immediate actions

| # | Action | Owner | Blocks |
|---|---|---|---|
| 1 | **Resolve the vendor order-window conflict** between the docx and the 2026 xlsx | Taylor | Scheduling engine (P0) + the published quick-reference guide |
| 2 | Generate a MarginEdge API key and read `developer.marginedge.com`; confirm whether **invoices** are an exposed resource | Taylor (Admin) | Recommendations 2, 3, 5 |
| 3 | Confirm whether MarginEdge beverage recipe/PMIX mapping is configured for Short North | Taylor | Whether Theoretical On-Hand is usable |
| 4 | Re-authorize the Gmail and Google Drive connectors (expired tokens) | Taylor | Future searches only |
