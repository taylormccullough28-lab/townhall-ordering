# PRD: TownHall Beverage Order Assistant

**Status:** Draft — pre-build · **Owner:** Taylor McCullough · **Last updated:** 2026-08-29

**Location scope:** TownHall Columbus, 792 N High St, Columbus OH 43215. Single location.

**Source documents:** `TH_ORDER_GUIDE.docx` (vendor list, order windows, delivery days, product-to-distributor mapping, receiving procedure). The vendor calendar and product catalog in that guide are the seed data for this system.

**Scope decisions (confirmed):**
- Columbus only. The CLE guest-ordering PRD (`PRD.md`) is a separate product — this one is internal purchasing, not guest-facing, and shares no surface with it.
- Beverage only. Food, paper, and chemical ordering are out of scope.
- This replaces the third-party inventory service (Sculpture Hospitality / Intellipar), which is being discontinued. Whatever this system does not cover, nobody covers.

---

## Problem Statement

Ordering beverage for TownHall Columbus currently runs on a manager's memory, a walk of the cooler, and a third-party count report — and that report is going away. Six vendors have six different order windows spread across four days of the week, each with its own delivery day, and missing one window means going without that vendor's product for a full week. The order itself is built by eyeballing what looks low, with no read on what actually sold, and no systematic adjustment for the things that reliably move volume in the Short North: OSU home games, Blue Jackets home games, Gallery Hop, buyouts, and hot weather.

The result is both failure modes at once. We run out of fast movers on the biggest nights of the year, and we carry dead stock on slow SKUs that tie up cash and cooler space we don't have. Nobody can say afterward whether an order was right, because there is no record of what the order was based on.

The data to solve this already exists — the POS knows exactly what sold, and the calendar knows what's coming — it's just never been put in front of the person building the order.

## Goals

- Turn last week's POS sales export into a concrete, per-vendor order sheet in under 15 minutes, versus the ~60–90 minutes of counting and guessing it takes now.
- Adjust order quantities for known demand drivers — OSU and Blue Jackets home games, Gallery Hop, private buyouts, weather, promos — rather than ordering a flat week every week.
- Never miss an order window. The system knows Sunday 7pm, Monday 4pm, Monday 5pm, Wednesday 5pm, Wednesday 9pm and Thursday 5pm, and pushes the manager before each one.
- Order to the *next delivery*, not to a flat seven days — a Southern Glazer's Tuesday drop has to cover eight days if the Wednesday follow-up isn't placed, and a Superior Monday drop only has to cover four if the Thursday window is used.
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

**1. Drop in the sales report.** Manager exports last week's product-mix report from the POS and uploads the CSV/XLSX. The system parses item names and quantities by day. Anything it can't map to a known product lands in an **unmapped queue** — the manager maps it once and it stays mapped.

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
| **Wine by the glass** | 750ml = 25.4 oz; a 5oz pour yields **5 glasses per bottle** with spill allowance. Cases of 12. |
| **Spirits in cocktails** | Recipe spec × drinks sold, summed across every drink containing that spirit. 750ml = 25.4 oz, 1L = 33.8 oz. |
| **Prep ingredients** | Same as spirits, via recipe. This is how Chinola, Llords Elderflower and Mr. Boston Triple Sec get forecast — they never appear on a POS line of their own. |

Draft partial kegs: V1 does not weigh kegs. The manager marks each tapped keg **full / ¾ / ½ / ¼ / blowing** and the system converts to remaining ounces. Crude, but it's the difference between ordering blind and ordering close.

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
                 window is used; Southern Glazer's Tue→Tue is 7, or 8 if the
                 Wednesday follow-up isn't placed)

need      = forecast_over_cover + safety_stock − on_hand − already_on_order
safety    = 25% of forecast_over_cover, floored at 1 unit  (V1 flat rule)
order_qty = round_up_to_pack(need), subject to vendor minimum
```

Safety stock as a flat 25% is deliberately simple for V1. The statistically correct version — `z × σ(weekly demand)`, sized per item by how volatile it is — needs demand history the system won't have on day one.

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
| Sales report ingest | Accepts CSV and XLSX export from the POS. Parses item name, quantity, and date. Unrecognized items go to an unmapped queue rather than being silently dropped. |
| Product catalog | All products from the order guide, each with vendor, category, pack size, unit size, and par. Editable without a code change. |
| Menu-item → SKU mapping | Every POS item maps to one or more catalog products with a conversion factor. Recipe-based mapping supported for cocktails and prep ingredients. Admin UI, no engineering required. |
| Count entry | Mobile-friendly entry for the order-critical list. Saves partial progress. Shows last week's count for reference. |
| Event calendar | OSU home football, Blue Jackets home, and Gallery Hop pre-seeded for the season. Manual add for buyouts, promos and specials. Per-day multiplier editable. |
| Order suggestion engine | Produces per-vendor quantities using the math above, rounded to pack size, covering to the next delivery for that vendor. |
| Reasoning line | Every suggested quantity shows: units sold last week, applied multipliers, on hand, days of cover, resulting order. |
| Manual override | Any quantity is editable. Overrides persist and are recorded against the order. |
| Order windows & reminders | Six windows encoded. Countdown per vendor. Notification ahead of each cutoff to the ordering manager. |
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
2. **Which POS, and what does its product-mix export actually contain?** Everything in stage 1 depends on the real export format — item granularity, whether modifiers are broken out, whether comps and voids are separated.
3. **What are the actual pour sizes?** Draft in pints or 16oz? 12oz for high-ABV? Wine at 5oz or 6oz? Every draft and wine number is wrong until these are confirmed.
4. **Do cocktail recipes exist in writing?** Spirit and prep-ingredient forecasting requires specs. If they aren't documented, that's a prerequisite project, not a feature.
5. **Who owns the mapping upkeep?** New menu items and keg rotations break the mapping continuously. Without a named owner this degrades within a season.
6. **What did Sculpture actually deliver that we still need?** Before the engagement ends: get back historical count data, par levels, and the item catalog. Some of it is seed data for this system.
7. **Does this ever extend to CLE?** Affects whether the catalog is built single-tenant or multi-tenant from the start.

## Timeline Considerations

Rough sequencing, not committed dates.

- **Phase 0 — Prerequisites.** Confirm the POS export format, pour sizes, and cocktail specs. Extract whatever is recoverable from Sculpture before the engagement closes. Nothing else can start cleanly without this.
- **Phase 1 — Catalog and mapping.** Load the order guide's products, vendors and windows. Build the mapping admin. Map the current menu. This is the largest single chunk of work and it is unglamorous.
- **Phase 2 — Count and suggest.** Count entry, depletion math, order suggestion, reasoning lines, per-vendor output. This is the first version that saves anyone time.
- **Phase 3 — Events and forecast.** Event calendar, multipliers, weather. This is where "order based off of events" actually lands.
- **Phase 4 — Receiving and history.** Receiving checklist, keg return tracking, order history, stockout and dead-stock reporting.

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
