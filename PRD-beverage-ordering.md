# PRD: TownHall Beverage Order Assistant

**Status:** Draft — pre-build · **Owner:** Taylor McCullough · **Last updated:** 2026-08-29

**Location scope:** TownHall Columbus, 792 N High St, Columbus OH 43215. Single location.

**Source documents:** `TH_ORDER_GUIDE.docx` (vendor list, order windows, delivery days, product-to-distributor mapping, receiving procedure). The vendor calendar and product catalog in that guide are the seed data for this system.

**Scope decisions (confirmed):**
- Columbus only. The CLE guest-ordering PRD (`PRD.md`) is a separate product — this one is internal purchasing, not guest-facing, and shares no surface with it.
- Beverage only. Food, paper, and chemical ordering are out of scope.
- This replaces the third-party inventory service (Sculpture Hospitality / Intellipar), which is being discontinued. Whatever this system does not cover, nobody covers.
- **Sales input is Toast, Monday through Sunday of the prior week.** Confirmed. Manual export in V1 — no Toast connector exists in Claude's registry and no scheduled Toast export exists in the account today. Report selection (ItemSelectionDetails vs. PMIX) is pending a Short North sample; see the ingest appendix.

---

## Problem Statement

Ordering beverage for TownHall Columbus currently runs on a manager's memory, a walk of the cooler, and a third-party count report — and that report is going away. Six vendors have six different order windows spread across four days of the week, each with its own delivery day, and missing one window means going without that vendor's product for a full week. The order itself is built by eyeballing what looks low, with no read on what actually sold, and no systematic adjustment for the things that reliably move volume in the Short North: OSU home games, Blue Jackets home games, Gallery Hop, buyouts, and hot weather.

The result is both failure modes at once. We run out of fast movers on the biggest nights of the year, and we carry dead stock on slow SKUs that tie up cash and cooler space we don't have. Nobody can say afterward whether an order was right, because there is no record of what the order was based on.

The data to solve this already exists — the POS knows exactly what sold, and the calendar knows what's coming — it's just never been put in front of the person building the order.

## Goals

- Turn last week's POS sales export into a concrete, per-vendor order sheet in under 15 minutes, versus the ~60–90 minutes of counting and guessing it takes now.
- Adjust order quantities for known demand drivers — OSU and Blue Jackets home games, Gallery Hop, private buyouts, weather, promos — rather than ordering a flat week every week.
- Never miss an order window. The system knows all seven cutoffs — Sunday 5pm and 7pm, Monday 4pm and 5pm, Wednesday 5pm and 9pm, Thursday 5pm — and pushes the manager before each one.
- Order to the *next delivery*, not to a flat week — a Superior Monday drop only has to cover four days if the Thursday window is used, while a Southern Glazer's Tuesday drop has to cover the full seven to the next Tuesday, plus whatever buffer the vendor's reliability warrants.
- Replace the Sculpture engagement with a count short enough that a manager actually does it — an order-critical list, not a full inventory.
- Make every ordered quantity explainable in one line: what sold, what's coming, what's on hand, what we're ordering and why.
- Capture the keg credits we're owed by making empty-keg return a required field on receiving, not a reminder someone ignores.

## Non-Goals

- **Not a full inventory or COGS system.** It does not do full-bar valuation, pour cost by category, or variance investigation. It answers "what do I order," not "where did the liquor go."
- **Not an EDI or vendor-API integration.** V1 produces a draft order the manager sends by the channel each vendor already uses — email for Arena, phone or text for the reps. No vendor is being asked to change how they take orders.
- **Not a POS replacement,** and not live-integrated with the POS in V1. The manager exports a sales report and drops it in.
- **Not a food or supply ordering system.** Beverage only.
- **Not a scheduling, labor, or event-management tool.** It reads the events calendar; it does not own it.
- **Not multi-location.** Columbus only. CLE and any other location would need their own vendor catalog and are explicitly out of scope.
- **Not an auto-send.** The system never places an order on its own. A human reviews and sends every order, every time.
- **Not a par-level oracle.** It suggests par revisions from observed demand, but a human sets par.

## Target Users

- **Primary: the manager on the ordering shift.** Not necessarily the same person each week. Needs to build a correct order for an unfamiliar vendor without knowing the history — the system has to carry the institutional knowledge that currently lives in one person's head.
- **Secondary: the GM / beverage director.** Reviews what was ordered and why, sets par levels, approves the event multipliers, watches for over-ordering and dead stock.
- **Secondary: the manager receiving a delivery.** Different shift, different person. Needs the count-in checklist and the empty-keg return field on their phone at the dock.
- **Internal: whoever maintains the product mapping.** Every new menu item, keg rotation, or SKU change has to get mapped to a vendor product or the math silently under-orders. This is a real, recurring job and needs an owner.

## User Stories

- As the ordering manager, I want to drop in last week's POS sales export and get a suggested order per vendor, so I'm starting from data instead of a blank page.
- As the ordering manager, I want to enter counts for a short order-critical list on my phone while walking the cooler, so the suggestion accounts for what's actually on the shelf.
- As the ordering manager, I want to mark next Saturday as an OSU home game and see the light beer and seltzer quantities move, so I don't get caught short on the biggest night of the week.
- As the ordering manager, I want each suggested quantity to show its reasoning — sold 187 last week, +60% for the OSU game, 3 cases on hand, order 6 — so I can sanity-check it rather than trust it blindly.
- As the ordering manager, I want to override any quantity and have the system keep my number, so the tool never blocks me from using judgment.
- As the ordering manager, I want a reminder before each order window with the vendors due, so a Sunday 7pm cutoff doesn't slip past on a busy service.
- As the ordering manager, I want the Arena order to come out as an email body addressed to arenaliquor@gmail.com, because that vendor does not take orders by phone or text.
- As the ordering manager ordering OYO, I want the system to route me to Arena first and only surface Zack's number if I mark Arena out of stock, so we follow the supplier agreement.
- As the ordering manager ordering Sixth City or Cavalier, I want a style-and-quantity recommendation (four 1/6 bbls, sours and pale ales) rather than specific SKUs, because those lines rotate and I have to ask the rep what's available.
- As the receiving manager, I want a count-in checklist on my phone with the expected quantities, so I can verify against the invoice before signing.
- As the receiving manager, I want empty kegs returned to be a required entry, so we stop eating the credits when a driver skips the pickup.
- As the GM, I want to see which items we stocked out of and which we over-ordered last month, so I can revise par with evidence.
- As the GM, I want to see the difference between what the POS says we sold and what we actually depleted, so I can catch the gap the Sculpture reports used to surface.

## How It Works

Five stages. Each one is a screen.

**1. Drop in the Toast PMIX.** Manager exports the PMIX report for the prior Monday–Sunday and uploads the CSV. The system filters to beverage sales categories, parses item names and quantities, and drops anything it can't map into an **unmapped queue** — the manager maps it once and it stays mapped. See the PMIX appendix for the expected shape.

**2. Count the order-critical list.** A short list — the fast movers, the kegs on tap, the prep ingredients — entered on a phone while walking the keg cooler, back bar, walk-in and dry storage. Not a full inventory. Target: under 10 minutes, roughly 40–60 lines.

**3. Confirm the week ahead.** The system pre-loads OSU home football, Blue Jackets home games, and Gallery Hop (first Saturday). The manager adds buyouts, private events, promos and specials, and confirms or overrides the weather read.

**4. Review the order.** One card per vendor, grouped by order window, each with a countdown to cutoff. Every line shows the suggested quantity, the reasoning, and an override field. Vendor-specific rules are applied here — email-only for Arena, style-not-SKU for the rotating lines, the Southern Glazer's follow-up prompt.

**5. Send and receive.** Copy-to-clipboard or email draft per vendor. The order is saved, so when the delivery arrives the receiving manager gets a count-in checklist with expected quantities and a required empty-keg return count.

## The Math

This is the core of the product and the part most likely to be wrong on the first build. Spelling it out.

### Depletion — converting POS sales to product units

The POS sells *menu items*; vendors sell *SKUs*. The mapping between them is the heart of the system.

| Product type | Conversion |
|---|---|
| **Packaged beer / RTD** | 1 sold = 1 unit. `cases = units ÷ pack_size` (Bud Light 24, Mich Ultra Gold 12, Nutrl 6, Pacifico 16oz 6/4pk) |
| **Draft** | `oz_sold = pours × pour_size`. Usable yield after ~5% foam and line loss: **1/2 bbl ≈ 1,880 oz (~117 pints)**, **1/6 bbl ≈ 627 oz (~39 pints)** |
| **Wine by the glass** | 750ml = 25.36 oz ÷ 5oz pour = 5.07 theoretical glasses. Apply the overpour factor as with spirits; do **not** also round down to "5 glasses with spill allowance" — that double-counts the same loss. Cases of 12. |
| **Spirits, poured** | `oz = qty × pour_size`, where pour size comes from the **modifier report** — see the pour table below. Default to Single when no pour modifier is present. |
| **Spirits in cocktails** | Recipe spec × drinks sold, summed across every drink containing that spirit. |
| **Bottle service** | **1 sold = 1 whole bottle.** Not a pour, not a recipe. Plus any bundled mixers. See below — this one breaks the model if handled wrong. |
| **Prep ingredients** | Same as cocktails, via recipe. This is how Chinola, Llords Elderflower and Mr. Boston Triple Sec get forecast — they never appear on a POS line of their own. |

### Standard pours and bottle yields

Confirmed house pours:

| Pour | Size | 750ml bottle yields | 1L bottle yields |
|---|---|---|---|
| **Single** | 1.5 oz | 16.9 | 22.5 |
| **Rocks** | 2.5 oz | 10.1 | 13.5 |
| **Double** | 3.0 oz | 8.4 | 11.3 |

Reference: 750ml = 25.36 oz, 1L = 33.81 oz, 1.75L = 59.17 oz.

These yields are theoretical. Real depletion runs higher, and the system applies a configurable **overpour factor** per bar rather than baking a number in — `effective_yield = theoretical_yield ÷ (1 + overpour)`. A free-pouring bar typically loses meaningfully more than a jiggered one, so the factor is a setting, seeded at 5% and corrected once the count data shows the true gap.

Draft partial kegs: V1 does not weigh kegs. The manager marks each tapped keg **full / ¾ / ½ / ¼ / blowing** and the system converts to remaining ounces. Crude, but it's the difference between ordering blind and ordering close.

### Bottle service

Bottle service is the single most dangerous item type in this model, and it needs its own handling:

- **A bottle service sale depletes a whole bottle, not a pour.** If a bottle service line is mapped like a cocktail or a pour, the system under-counts that spirit's depletion by a factor of ten or more. Bottle service items get an explicit `whole_bottle` conversion type.
- **Bundled mixers deplete too.** A bottle service package that includes Red Bull, juice or soda depletes those alongside the spirit. The bundle contents are part of the mapping, not an afterthought.
- **It must be excluded from the trailing-average baseline.** Bottle service is lumpy and event-driven — one buyout can move more Grey Goose in a night than a normal month of cocktails. Left in the four-week average, a single big night inflates the forecast for a month and the bar over-orders premium spirits it won't touch. Bottle service is forecast from the **events calendar** (known bookings, expected VIP nights), not from trailing sales.
- **Premium bottles are the highest-dollar exposure in the bar.** Ace of Spades and Dom Pérignon are already flagged "not ordered frequently" in the order guide — those are almost certainly bottle-service-only SKUs, and getting them wrong is expensive in both directions.

### Forecast — what next week looks like

```
baseline(item, weekday) = trailing 4-week mean of that item on that weekday, outlier-trimmed

forecast(item) = Σ over the next 7 days of:
    baseline(item, weekday)
  × event_multiplier(day)
  × weather_multiplier(day, category)
  × promo_multiplier(item, day)
```

V1 multipliers are **manual, editable defaults** — not learned. Seed values, to be tuned against real results:

| Driver | Effect |
|---|---|
| OSU home football, day of | +60% overall; +90% domestic/light beer and seltzer |
| Blue Jackets home game | +25% overall |
| Gallery Hop (first Saturday) | +35% |
| Private buyout | headcount × per-head rate, overrides baseline for that day |
| Temp > 85°F and sunny | +20% seltzer, light beer, draft; −10% red wine and brown spirits |
| Temp < 40°F | −15% seltzer; +15% brown spirits |
| Feature / promo on an item | manual, set per promo |

Once there are ~6 months of history, these coefficients should be fit from TownHall's own sales rather than guessed — a regression on weekday, event flags and temperature. That's V3, not V1.

### Order quantity

```
days_of_cover = days until the NEXT delivery from this vendor
                (not a flat 7 — Superior Mon→Fri is 4 days if the Thursday
                 window is used; Southern Glazer's Tue→Tue is 7)

cover_days    = gap_days + cover_buffer_days   # buffer configurable per vendor,
                                               # default 0; use it for vendors
                                               # whose delivery slips, not to
                                               # fudge the gap arithmetic

need      = forecast_over_cover + safety_stock − on_hand − already_on_order
safety    = 25% of forecast_over_cover, floored at 1 unit  (V1 flat rule)
          # WARNING: applied literally, a zero-demand SKU with zero on hand
          # orders a full case every week. See Open Question 12.
order_qty = round_up_to_pack(need), subject to vendor minimum
```

Safety stock as a flat 25% is deliberately simple for V1. The statistically correct version — `z × σ(weekly demand)`, sized per item by how volatile it is — needs demand history the system won't have on day one.

### Adjusting for business that happens after the cutoff

The PMIX week runs Monday–Sunday, but three vendors are ordered **Sunday between 5:00 and 7:00 PM** (Arena 5pm, Superior and Columbus Dist. 7pm) and three more **Monday between 4:00 and 5:00 PM** (Southern Glazer's 4pm, Sixth City and Cavalier 5pm). Those orders are placed while the bar is still open and still selling, and the delivery doesn't arrive until the next morning. A count taken Sunday afternoon therefore overstates what will actually be on the shelf when Monday's truck shows up — by a full Sunday night of business, which for a Short North bar is not a rounding error.

```
effective_on_hand = counted_on_hand − projected_sales(cutoff → delivery)

where projected_sales uses the same baseline × multiplier model,
prorated for the remaining hours of the shift
```

Worked: counting 4 cases of Bud Light at 4pm Sunday, with Sunday nights averaging 30 bottles after 5pm, means Monday's truck is really landing against 2.75 cases, not 4. Without this adjustment the system under-orders every Sunday and every Monday — the two heaviest ordering days on the calendar.

The same logic makes the **Monday–Sunday PMIX window the right choice**: it is the most recent *complete* week available at the Sunday cutoff. Pulling a week that includes the in-progress Sunday would double-count it — once as partial history, once as projected depletion.

### Vendor rules encoded from the guide

- **Arena Liquor** — output is an email body to arenaliquor@gmail.com. The system will not produce a text or call script for Arena. Gursev's number appears only under an "emergency" label.
- **OYO Vodka** — always routes to Arena. Zack's contact is hidden unless the manager marks Arena out of stock.
- **Sixth City and Cavalier** — rotating lines, no fixed SKUs. Output is a style-and-count recommendation ("4 × 1/6 bbl, sours and pale ales — ask Jenna what's available"), never a specific product.
- **Southern Glazer's** — if the Tuesday order won't cover to next Tuesday, the system offers the Wednesday follow-up, flagged **"confirm with Bethany first — not guaranteed."**
- **Superior Beverage** — two windows. The system picks Sunday-only or Sunday-plus-Thursday based on whether a four-day cover meaningfully reduces the order size.
- **Heidelberg** — delivery note "after 9am, hallway behind bar" appears on the receiving checklist.
- **All keg vendors** — empty-keg return count is a required field before a delivery can be marked received.

## Requirements

### Must-Have (P0)

| Requirement | Acceptance Criteria |
|---|---|
| Toast sales ingest | Accepts Toast exports for a Monday–Sunday business-day range in both shapes: multi-sheet PMIX XLSX and line-item ItemSelectionDetails CSV. Matches columns by normalized header name, never position. Treats every column and sheet as optional. Filters `All levels` rows to `Type` in (menuItem, openItem) so rollup rows never double-count. Excludes voids; comps counted as depletion but stay flagged. Unrecognized items go to an unmapped queue rather than being silently dropped. |
| Beverage classification | Sales Category when present, falling back to the product mapping on Menu + Menu group + Item. Never category alone — blank categories occur on real liquor SKUs, and the same item can carry different categories on different menus. |
| Toast modifier ingest | Accepts the modifier report for the same range. Classifies every modifier as pour-size (replaces default pour) or product (adds a depletion line). Unclassified modifiers go to the unmapped queue. |
| Composite mapping key | Products map on Sales Category + Menu + Menu Group + Menu Item, not item name alone. Two same-named items on different menus stay distinct. |
| Pour size configuration | Single 1.5oz, Rocks 2.5oz, Double 3.0oz as defaults, editable. Configurable overpour factor per bar. Sales with no pour modifier default to Single. |
| Bottle service handling | Bottle service items deplete a whole bottle, carry their bundled mixers, and are excluded from the trailing-average baseline — forecast from the events calendar instead. |
| Post-cutoff depletion adjustment | For orders placed before the week's business is done (Sun 5–7pm, Mon 4–5pm), the system subtracts projected sales between the cutoff and the delivery from the counted on-hand. |
| Product catalog | All products from the order guide, each with vendor, category, pack size, unit size, and par. Editable without a code change. |
| Menu-item → SKU mapping | Every POS item maps to one or more catalog products with a conversion factor. Recipe-based mapping supported for cocktails and prep ingredients. Admin UI, no engineering required. |
| Count entry | Mobile-friendly entry for the order-critical list. Saves partial progress. Shows last week's count for reference. |
| Event calendar | OSU home football, Blue Jackets home, and Gallery Hop pre-seeded for the season. Manual add for buyouts, promos and specials. Per-day multiplier editable. |
| Order suggestion engine | Produces per-vendor quantities using the math above, rounded to pack size, covering to the next delivery for that vendor. |
| Reasoning line | Every suggested quantity shows: units sold last week, applied multipliers, on hand, days of cover, resulting order. |
| Manual override | Any quantity is editable. Overrides persist and are recorded against the order. |
| Order windows & reminders | Seven distinct cutoffs encoded across four days: Sun 5pm, Sun 7pm, Mon 4pm, Mon 5pm, Wed 5pm, Wed 9pm, Thu 5pm. Countdown per vendor. Notification ahead of each cutoff to the ordering manager. |
| Per-vendor output | Formatted order per vendor, matching that vendor's channel — email body for Arena, copy-paste text for phone/text vendors, style recommendation for rotating lines. |
| Receiving checklist | Expected quantities per delivery, count-in confirmation, shorts and damages noted, **required empty-keg return count**. |
| Order history | Every order saved with its inputs, suggestions, overrides and receipt. |

### Nice-to-Have (P1)

| Requirement | Acceptance Criteria |
|---|---|
| Weather auto-pull | Pulls the 7-day forecast for 43215 and applies the weather multiplier automatically, with manual override. |
| Stockout and dead-stock report | Flags items that hit zero before the next delivery, and items with no depletion over 30 days. |
| Par level suggestions | Recommends par revisions from observed demand. Human approves. |
| Invoice reconciliation | Enter what was actually delivered and invoiced; system reconciles against the order and flags shorts and price changes. |
| Theoretical vs. actual variance | Compares POS-implied depletion against counted depletion — the signal the Sculpture reports used to provide. |
| Keg credit tracker | Running count of empties returned versus credits received. |

### Future Considerations (P2)

- Live POS integration, removing the manual export step.
- Learned event and weather coefficients fit from TownHall's own history.
- Vendor price tracking and cost-per-ounce comparison across distributors.
- Multi-location, with a shared catalog and per-location vendor calendars.
- Photo-based or scale-based keg level reading instead of the full/¾/½/¼ estimate.

## Success Metrics

| Metric | Baseline | Target |
|---|---|---|
| Time to build a full week's orders | ~60–90 min | Under 15 min |
| Missed order windows per quarter | Unknown, believed non-zero | 0 |
| Stockouts of tracked fast movers per month | Not measured | Under 2 |
| Items with zero depletion in 30 days (dead stock) | Not measured | Trending down month over month |
| Empty kegs returned vs. kegs received | Not measured | Above 95% |
| Suggested quantities accepted without override | n/a | Above 70% by month 3 — the trust signal |
| Cost of the replaced inventory service | Sculpture monthly fee | $0 |

## Open Questions

1. **This is the big one: is a count still required?** A sales report alone cannot produce an order quantity — it tells you what left, not what's on the shelf. Two paths: **(a)** a short weekly count of order-critical items, which is what this PRD assumes, or **(b)** perpetual inventory, where the system tracks on-hand by subtracting depletion and adding receipts, with a full recount monthly to correct drift. Path (b) is less weekly work but accumulates error fast if any receipt or transfer goes unrecorded, and it needs an accurate starting count regardless. **Recommendation: build (a) first, add (b) as an option once the mapping is proven accurate.**
2. ~~Which POS?~~ **Resolved: Toast PMIX plus a modifier report, Monday–Sunday, 4:00 AM business-day close. Categories: Liquor, Beer, Wine, Cocktails. Comps counted, voids excluded.**
3. ~~Spirit pour sizes?~~ **Resolved: Single 1.5oz, Rocks 2.5oz, Double 3.0oz.** Still open: **wine by the glass** (5oz or 6oz — a 25% swing per bottle) and **draft** (16oz throughout, or 12oz for high-ABV).
4. **How do the reports actually reach the app?** No Toast connector exists in Claude's registry, and no scheduled Toast export exists in the account — the only recurring Toast email is an HTML-body Daily Performance Summary with no attachment. Three options: manual upload (works today, V1 as specced); a **newly configured Toast scheduled export emailed to a dedicated inbox**, which first requires confirming Toast will attach a file rather than render it inline; or the Toast partner/developer API, which has real lead time. **Recommendation: build the parser against manual upload, then move to scheduled email without changing the parser.**
5. ~~Where do non-alcoholic items live?~~ **Likely `NA Beverage`** — that category exists in the recovered exports. Confirm it is the label used at Short North, since filtering it out would mean never ordering Red Bull.
6. **Do cocktail recipes exist in writing?** Spirit and prep-ingredient forecasting requires specs. If they aren't documented, that's a prerequisite project, not a feature.
7. **Free-pour or jiggered?** Sets the starting overpour factor, which moves every spirit quantity in the system.
8. **What's in each bottle service package?** Bundled mixers have to be enumerated per package to deplete correctly.
9. **Who owns the mapping upkeep?** New menu items and keg rotations break the mapping continuously. Without a named owner this degrades within a season.
10. **What did Sculpture actually deliver that we still need?** Before the engagement ends: get back historical count data, par levels, and the item catalog. Some of it is seed data for this system.
11. **Does this ever extend to CLE?** Affects whether the catalog is built single-tenant or multi-tenant from the start.
12. **What should the safety-stock floor do on a dead SKU?** "25% of forecast, floored at 1 unit" applied literally means an item that sold nothing, with none on hand, still orders a full case — a dead-stock generator. Options: suppress the floor below a demand threshold, floor at zero when trailing demand is zero, or keep the floor only for items flagged must-never-86. **Recommendation: floor at zero when four-week demand is zero, and warn rather than order.**
13. **Do vendors take partial cases?** `round_up_to_pack` currently rounds to whole packs, so a need of 25 Bud Light bottles buys 2 cases. Confirm per vendor — some allow splits, and rounding a 25-bottle need up to 48 is a real cost.
14. **How is a bottle-service forecast entered?** "Forecast from the events calendar" has no defined input. Currently wired to explicit booked-bottle counts per event day. Confirm that matches how bookings actually arrive.
15. **What triggers the Southern Glazer's Wednesday follow-up?** "When Tuesday won't cover" is not a condition the engine can evaluate — with round-up-to-pack, an uncapped order always covers. Currently triggered by a real shortfall against a per-delivery cap, or a manager override.
16. **Buyout per-head consumption rates.** The formula is specced; the rates are not. A buyout event currently raises rather than silently forecasting zero.

## Timeline Considerations

Rough sequencing, not committed dates.

- **Phase 0 — Prerequisites.** Pull one real Toast PMIX export and one modifier export, and answer the remaining questions in the ingest appendix. Confirm wine and draft pour sizes and cocktail specs. Extract whatever is recoverable from Sculpture before the engagement closes. Nothing else can start cleanly without this.
- **Phase 1 — Catalog and mapping.** Load the order guide's products, vendors and windows. Build the mapping admin. Map the current menu. This is the largest single chunk of work and it is unglamorous.
- **Phase 2 — Count and suggest.** Count entry, depletion math, order suggestion, reasoning lines, per-vendor output. This is the first version that saves anyone time.
- **Phase 3 — Events and forecast.** Event calendar, multipliers, weather. This is where "order based off of events" actually lands.
- **Phase 4 — Receiving and history.** Receiving checklist, keg return tracking, order history, stockout and dead-stock reporting.

## Appendix: Toast Report Ingest

**Evidence base:** two real Toast PMIX exports and one ItemSelectionDetails CSV recovered from the company OneDrive. Verbatim headers and sample rows below are from those files. **Important caveat: both PMIX exports are from FWD Day & Nightclub, a different concept in the same Toast account family.** The single TownHall file is a 2023 CLE export. Nothing recovered is a TownHall Short North beverage export, so the *structure* below is trustworthy and the *category values* are not yet confirmed for our location.

### The format is a multi-sheet workbook, not a flat CSV

Toast's PMIX exports as XLSX with up to eight sheets: `Summary`, `All levels`, `Menus`, `Menu groups`, `Items`, `Open items`, `Modifiers`, `Special requests`.

Two sheets matter:

| Sheet | Observed header row |
|---|---|
| `Items` | `Item \| Sales Category \| Qty sold` |
| `All levels` | `Type \| Menu \| Menu group \| Item, open item \| Qty sold` |

The `All levels` sheet is the one that carries menu structure, which the composite mapping key needs.

### Three hard-won parser rules

**1. Match columns by header name, never by position — and treat every column as optional.** The two recovered exports have *different column sets from the same account*, because sheets and columns are selected at export time. One has `Sales Category` on the `Items` sheet; the other has no `Sales Category` column anywhere. One has a `Subgroup` column on `All levels`; the other doesn't. One has `Modifiers` and `Special requests` sheets; the other omits both entirely. A positional parser breaks on the second file it ever sees.

**2. Filter `All levels` on `Type`, or double-count everything.** Rollup rows have a blank `Type`; leaf rows carry `menuItem` or `openItem`. Observed:

```
Type        Menu              Menu group      Item, open item        Qty sold
menuItem    LIQUOR            Tequila         Espolon BLANCO         193
menuItem    COCKTAIL          FWD Cocktails   PassionPunch Margarita  34
openItem    Open items        Open Drink      Lobos Blanco Bottle      3
```

Only `menuItem` and `openItem` rows are real sales. Everything else is a subtotal.

**3. Sales Category cannot be the only beverage filter.** Blank categories are common and include *genuine liquor SKUs* — one observed row is `Bacardi FB`, qty 4, with no category at all. Filtering on category alone silently drops real depletion. The filter must be: category when present, falling back to the explicit product mapping keyed on Menu + Menu group + Item.

### Observed Sales Category values — and how they differ from expectation

Complete observed set across both accounts: `Liquor` · `Bottled Beer` · `NA Beverage` · `Champagne` · `Bottle Service` · `Cigars` · `Retail` · `Room Rental` · `Food` · *(blank)*

Against the four categories assumed earlier (Liquor, Beer, Wine, Cocktails):

- **No `Beer`** — it's `Bottled Beer`, and it absorbs seltzers and RTDs (Nutrl, Suncruiser) and at least one miscategorized chardonnay.
- **No `Wine`** category appears at all. `Champagne` exists separately.
- **No `Cocktails`** category. Cocktails roll up to `Liquor` and are only identifiable by `Menu` or `Menu group`. This is further reason the mapping key is composite rather than category-based.
- **`NA Beverage` is the non-alcoholic label** — this answers where Red Bull, N/A beer and juice live. They are in the data, under a category name that would have been filtered out.
- **`Bottle Service` is its own category.** Convenient: the whole-bottle conversion type can key off it directly rather than needing manual tagging.

**These values come from FWD, not TownHall Short North.** They may well differ at our location. What is *structurally* certain is that the categories are not the four assumed, that blanks occur, and that cocktails are not separately categorized.

### The same item can carry different categories on different menus

From the TownHall CLE ItemSelectionDetails export — one item, one day, four categories and menus:

```
Location,Order #,Sent Date,Menu Item,Menu Group,Menu,Sales Category,Net Price,Qty,Void?
TH Ohio City,17,8/27/2023 9:06,Acai Bowl,SMOOTHIES,ONLINE BRUNCH,NA Beverage,16,2,FALSE
TH Ohio City,66,8/27/2023 9:54,Acai Bowl,Brunch Plates,BRUNCH,Food,8.75,1,FALSE
TH Ohio City,1240,8/27/2023 19:10,Acai Bowl,Smoothies,ONLINE 3RD PARTY,NA Beverage,8.75,1,FALSE
```

The same product classified as both `NA Beverage` and `Food` depending on which menu rang it. This validates the composite mapping key and rules out any name-only or category-only approach.

### ItemSelectionDetails may be the better input

The `ItemSelectionDetails` export is line-item level — **one row per sale, with a timestamp** — versus PMIX, which is aggregated for the whole range.

```
Location,Order #,Sent Date,Menu Item,Menu Group,Menu,Sales Category,Net Price,Qty,Void?
```

That timestamp matters more than it first appears. **The post-cutoff depletion adjustment needs to know how much sells between a 5:00 PM Sunday order cutoff and 4:00 AM close.** PMIX cannot answer that — it has no time dimension. ItemSelectionDetails can, and it also carries an explicit `Void?` flag and `Location`, which matters in a multi-location Toast account.

**Recommendation: pull ItemSelectionDetails as the primary input and PMIX as a cross-check on totals.** To be confirmed once we see a Short North export of each.

### Modifier data does not exist yet

No modifier-level export exists anywhere in the account. In the one PMIX that *has* a `Modifiers` sheet, **the sheet is empty**; the other export omits it. The ItemSelectionDetails CSV has no modifier rows and no parent-selection column.

One column name confirms Toast tracks it — `Avg. item price (not incl. mods)` — so the data exists in Toast and simply has not been exported. **This must be pulled fresh. There is nothing to build against today**, and without it every spirit defaults to a 1.5oz Single, which will undercount every rocks and double pour in the bar.

### No scheduled export exists to hook into

`no-reply@toasttab.com` sends a **Daily Performance Summary** once per day per location, and `Townhall - Short North` is among the active locations. But every one of these is an **HTML-body email with no attachment** — there is no recurring CSV or XLSX delivery anywhere in the account. The two PMIX files on OneDrive were manual downloads someone saved.

So the "scheduled email into an inbox" automation path requires **setting up a new scheduled export in Toast first**, and confirming Toast will attach PMIX/ItemSelectionDetails as a file rather than rendering it in the body. Until that is verified, manual upload is the only working path.

### What to pull from Short North

1. **ItemSelectionDetails**, prior Mon–Sun, Short North only.
2. **PMIX**, same range, **with the `Sales Category` column and the `Modifiers` sheet both checked on at export.**
3. **The modifier report**, same range — whatever Toast labels it in this account.

### Still to confirm

1. **Actual Sales Category values at Short North.** The FWD set above is indicative, not authoritative.
2. **Free-pour or jiggered?** Sets the overpour factor, which moves every spirit quantity.
3. **Wine by the glass pour size** — 5oz or 6oz. A 25% swing per bottle.
4. **Draft pour sizes** — 16oz throughout, or 12oz for high-ABV.
5. **What's in each bottle service package?** Bundled mixers must be enumerated per package.

---

## Appendix: Vendor Order Windows

Seed data for the scheduling engine. Source: `TH_ORDER_GUIDE.docx`.

| Vendor | Order due | Delivers | Channel | Notes |
|---|---|---|---|---|
| Superior Beverage | Sun 7:00 PM | Mon | Phone — Shane (614) 306-4582 | Second window: Thu 5:00 PM → Fri |
| The Columbus Dist. Co. | Sun 7:00 PM | Mon | Phone — Conner (937) 581-1234 | |
| Arena Liquor | Sun 5:00 PM | Mon | **Email only** — arenaliquor@gmail.com | Second window: Wed 9:00 PM → Thu 5 PM |
| Southern Glazer's of OH | Mon 4:00 PM | Tue | Phone — Bethany (740) 507-1973 | Wed follow-up → Fri possible, confirm first |
| Sixth City Distributors | Mon 5:00 PM | Tue | Phone — Jenna Carelly (614) 301-4877 | Rotating 1/6 bbl only |
| Cavalier Distributing | Mon 5:00 PM | Tue | Phone — Dan (614) 582-0014 | Rotating 1/6 bbl only |
| Heidelberg / Wine Trends | Wed 5:00 PM | Thu PM | Phone — Tess Canby (740) 583-4555 | Deliver after 9am, hallway behind bar |
| OYO Vodka | As needed | As needed | Phone — Zack (614) 981-9341 | **Order through Arena first** |
