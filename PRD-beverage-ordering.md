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
- Never miss an order window. Order days confirmed by the operator 2026-09-28/29: **Sunday** — Arena 5pm, Berardi's 5pm, Superior 7pm, Columbus Dist. 7pm; **Monday** — Southern Glazer's 4pm, Sixth City 5pm, Cavalier 5pm; **Wednesday** — Heidelberg 5pm, Superior 7pm (second window), Arena 9pm (second window); **Thursday** — Hillcrest 4pm (both accounts &mdash; the largest single cutoff in the building) and Hartzler 5pm, an hour apart. Sunday is the heaviest night at four vendors, and its 5:00 PM pair is the tightest cutoff of the week. Deliveries cluster hard on **Tuesday** — six vendors land the same morning (Superior, Columbus Dist., Berardi's, Southern Glazer's, Cavalier, Hartzler) while **Monday arrives empty**.
- Order to the *next delivery*, not to a flat week — a Superior Tuesday drop only has to cover three days if the Friday window is used, while a Southern Glazer's Tuesday drop has to cover the full seven to the next Tuesday, plus whatever buffer the vendor's reliability warrants.
- Replace the Sculpture engagement with a count short enough that a manager actually does it — an order-critical list, not a full inventory.
- Make every ordered quantity explainable in one line: what sold, what's coming, what's on hand, what we're ordering and why.
- Keep empty-keg return a required field on receiving. **Measured over a full quarter, this is not working at Superior.** Superior charged **117 keg deposits and credited back 84** over 2026-06-30..09-22 — **33 kegs, $990 outstanding** — and the balance drifts rather than oscillates: near zero through July, then +11, +17, +25, +33. Two invoices did most of it (2026-08-21: six bought, none returned; 2026-09-18: seven bought, none returned). Columbus Distributing over the same quarter is 34 paid / 36 returned, a $60 credit — a working return loop, and proof the process can hold. **A one-month window cannot see this**: an unreturned keg never comes back as a negative, it just stops appearing, so a month only shows the current week's exchange. The requirement exists to stop that drift, and to catch the two counting leaks the invoices show — kegs delivered with no deposit line charged, and a deposit line one vendor spells six different ways.

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

The PMIX week runs Monday–Sunday, but four vendors are ordered **Sunday between 5:00 and 7:00 PM** (Arena 5pm, Berardi's 5pm, Superior and Columbus Dist. 7pm) and three more **Monday between 4:00 and 5:00 PM** (Southern Glazer's 4pm, Sixth City and Cavalier 5pm). Those orders are placed while the bar is still open and still selling.

The corrected delivery schedule makes this gap **wider than one shift, not narrower**. Superior and Columbus Dist. are ordered Sunday 7pm but do not land until **Tuesday** — so the count behind that order has to survive Sunday night *and* all of Monday before the truck arrives. The Monday-cutoff vendors (Southern Glazer's, Sixth City, Cavalier) are the short case at one night. A count taken Sunday afternoon therefore overstates what will be on the shelf at receiving by up to **two full nights of business**, which for a Short North bar is not a rounding error.

```
effective_on_hand = counted_on_hand − projected_sales(cutoff → delivery)

where projected_sales uses the same baseline × multiplier model,
prorated for the remaining hours of the shift
```

Worked: counting 4 cases of Bud Light at 4pm Sunday, with Sunday nights averaging 30 bottles after 5pm and Mondays another 18, means **Tuesday's** truck is really landing against 2.0 cases, not 4 — the order is half again as large as a naive count would call for. Without this adjustment the system under-orders every Sunday and every Monday, the two heaviest ordering days on the calendar, and under-orders the Sunday vendors worst because theirs is the longest gap.

The same logic makes the **Monday–Sunday PMIX window the right choice**: it is the most recent *complete* week available at the Sunday cutoff. Pulling a week that includes the in-progress Sunday would double-count it — once as partial history, once as projected depletion.

### Vendor rules encoded from the guide

- **Arena Liquor** — output is an email body to arenaliquor@gmail.com. The system will not produce a text or call script for Arena. Gursev's number appears only under an "emergency" label.
- **Arena has two channels and only one of them is a schedule.** Wholesale invoices are prefixed `OH00028…` — 29 in the quarter, **$86,838 (96% of spend)**, averaging $2,994 across 12.5 lines, on the account number. Counter/will-call invoices are **6 digits** — 16 of them, $3,497 (4%), averaging $219 across 1.7 lines, usually with no account number, mostly Saturday: roughly **1.2 emergency runs a week**. The engine must forecast from the wholesale channel only. Feeding it the counter invoices would teach it a Saturday delivery that does not exist, and would hide the thing actually worth fixing — that someone drives to Arena once a week because something ran out.
- **Depletion is computed per vendor item code, never per product name.** Arena's codes end in `L` (1 litre) or `B` (750ml) and MarginEdge maps both onto one product, so product-level quantity silently adds sizes: Tito's reads **597 units** but is **444 × 1L + 153 × 750ml**. This affects **35% of Arena spend**, and on the largest line in the building the error is about **25%**. Four products also carry outright duplicate codes (`1809L_1L`/`1809L`, `2937L`/`2937L_Silver`, `2720B`/`2720B_ 750ML`, `0326L`/`0326L_1L`), which split a baseline across two keys so both read low. This is the same class of failure as the Albino Stout keg: **identity lives on the item code, not the name.**
- **Unattributable vendor spend is surfaced, never spread.** $2,878.93 of Arena's quarter — 3.2% — has no product attached: “Misc Liquor Item” and “Liquor” lines total $851.18, plus $2,027.75 of invoice-level charges, the largest being **$1,482.38 on 2026-08-20 described only as “Adjustment to match total”** — 39% of that invoice. Allocating it across products would inflate pour cost everywhere and hide it; it goes on an exceptions list for the manager to chase instead.
- **Duplicate-invoice detection blocks approval. This is not hypothetical: it already happened, for $5,781.06.** Two Arena invoices eight days apart — OH0002811019 (7/22) and OH0002821151 (7/30) — both total **$5,781.06** with **29 line items identical on code, quantity and price**. The operator confirmed on 2026-09-29 that it is a genuine **double bill**, now recoverable. It is **6.4% of the quarter's Arena spend**, and **nothing in MarginEdge flagged it** — it surfaced only by comparing line-item signatures across all 45 invoices. So: any invoice sharing a (code, quantity, price) signature with another from the same vendor **blocks** approval rather than warning. A warning on a $5.8K double bill is not enough. The pair also carried the account number two different ways (`727546` / `0727546`), so signature matching must ignore account formatting.
- **OYO Vodka** — always routes to Arena. Zack's contact is hidden unless the manager marks Arena out of stock.
- **Sixth City and Cavalier** — rotating lines. Output is a style-and-count recommendation ("4 × 1/6 bbl, sours and pale ales — ask Jenna what's available"), never a specific product.
- **Named SKUs on a style-only vendor** — a rotating vendor can still carry specific products. Any product flagged `named_sku` is ordered by name and **survives the rotating-line collapse**; only the remainder becomes a style-and-count. Cavalier currently carries one: Fat Head's Bumble Berry.
- **Dual-sourced products** — a product may list `alt_vendors`. This is advisory: the order is still built against the primary vendor, and the alternate is surfaced as a note. Nothing currently uses it.
- **Seasonal products** — a product carries `season` (year_round, summer, fall_winter). A seasonal item has **no trailing sales in the weeks before its launch**, so its baseline forecast is zero and the engine would order nothing. Seasonal launches fall back to **par, set by hand**, until two to three weeks of real sales accumulate. This is the same structural failure as bottle service, arriving twice a year on a predictable date.
- **Southern Glazer's** — if the Tuesday order won't cover to next Tuesday, the system offers the Wednesday follow-up, flagged **"confirm with Bethany first — not guaranteed."** **The follow-up is used more than "not guaranteed" suggests:** of 20 invoices over 2026-06-30..09-22, **12 landed Tuesday and 6 landed Friday**. It is a second ordering slot the bar already uses most weeks, not a favour Bethany might extend. The confirmation flag stays, because the window is still at her discretion — but the cover math must not assume Friday will be skipped.
- **Price increases have to be surfaced, because nobody is watching them.** Two moved on Southern Glazer’s this quarter with no flag anywhere: **Red Bull, regular (`201010`) and sugar-free (`0409127`), $42.00 → $46.00 a case, +9.5%**, and **Aperol 1L (`557367`), $142.00 → $156.95, +10.5%**. Red Bull is a weekly line, so that is a standing cost increase, not a one-off. The detection has to be **per vendor item code**, because the same product billed per-bottle on one invoice and per-case on another produces apparent swings of **+1,100%** — seven Heidelberg wines show exactly that, and they are pack-size artifacts, not price moves. Only a change within one packaging is a real increase; `911100` Frenzy Sauvignon Blanc at $127.95 → $135.95 (+6.3%) is one.
- **Superior Beverage** — two windows: Sunday 7pm for **Tuesday**, and **Wednesday 7pm for Friday** (moved from Thursday 5pm, confirmed 2026-09-21). The system picks Sunday-only or Sunday-plus-Wednesday based on whether a three-day cover meaningfully reduces the order size.
- **Heidelberg** — delivery note "after 9am, hallway behind bar" appears on the receiving checklist.
- **A vendor’s schedule can change mid-sample, and a longer window hides it rather than revealing it.** Heidelberg moved from Tuesday to Thursday on **1 September 2026**: all 19 invoices from 2026-06-30 through 08-25 are Tuesday, all 7 from 09-03 onward are Thursday, four consecutive weeks, no Tuesday since. Read across the whole quarter the split is **19 Tuesday / 16 Thursday**, which looks exactly like a vendor that delivers twice a week. It does not. This is the mirror image of the Busch Light error: **a one-month window made a new line look established, and a one-quarter window makes a changed schedule look like a two-day route.** Neither window length is safely "enough". The engine needs to **test for a changeover date before averaging any weekday distribution** — if the Tuesdays all precede a date and the Thursdays all follow it, that is one schedule that moved, not two schedules running at once, and only the later one is real.
- **Duplicate detection must normalise the invoice number, not just the line signature.** Heidelberg changed invoice numbering mid-August from seven digits (`9245930`) to nine (`900001202`), and during the cutover two invoices were recorded under **both** the bare sequence number and the prefixed one: `2919` (8/12, $175.95) = `900002919` (8/13, $185.95), and `4341` (8/13, $189.94) = `900004341` (8/13, $179.94). Both pairs carry **identical product lines at identical unit prices**; only the fee presentation differs — one copy carries the service and split-case charges in an invoice-level field, the other breaks them out as lines. **$365.89, uncredited.** The Arena double bill was caught by line signature; these two would also be caught that way, but the number itself is the cheaper check: **strip a leading `9000` and compare the tail.** The general rule is that a vendor changing its numbering scheme is a duplicate-invoice risk window, and the days around the change deserve a second look.
- **A matching total is not evidence of a double bill.** Checked against Buckeye on 2026-09-29: invoices `159063` (7/6) and `159345` (7/10) are each one Nitrogen Large at $61.45 four days apart — ordinary cylinder turnover — and `159994` (7/24) and `160054` (7/26) are Coca-Cola 5 GAL and Diet Coke 5GAL, two distinct products that happen to share a $142.78 price. Same class of false positive as the five Superlyte flavours and Sam Adams Cherry Wheat vs Lager. **The signature has to include the item code, and a human confirms before anything is chased.**
- **Buckeye Beverage supplies the draft gas, and it was missing from the catalog entirely until 2026-09-29.** 19 items, **$7,789.08 across 17 invoices**, more spend than Sixth City, Berardi’s, Hartzler or Cavalier — all of which were already modelled. It carries the fountain, every BIB mixer, the bar juices, and codes `1003` ("20# Pop") and `1010` ("50# Beer"), **the CO2 and nitrogen cylinders, billed at $0.00** under the STA program. A line that costs nothing is a line nobody reconciles, and when it runs out the draft system stops pouring, so **cylinder count belongs on the Monday receiving check** even though it never appears in spend.
- **How Buckeye was missed is a methodology defect, not an oversight.** The vendor list was transcribed from `TH_ORDER_GUIDE.docx` and then validated against a **top-12-by-spend ranking**. Buckeye ranks 13th. **Ranking inside a list you have already narrowed cannot find what the list left out** — every check confirmed the twelve vendors present and none could have surfaced a thirteenth. Vendors must be **enumerated from invoices** and reconciled against the written guide, in that direction. The same defect would hide any vendor below whatever cut-off the validation happens to use.
- **A vendor can have a known delivery day and no recordable cutoff.** Buckeye delivers **Monday** — 12 of 17 invoices, ~82% of spend, and every week in the quarter has a Monday invoice — but the order cutoff has never been recorded by anyone. It therefore carries **no order window at all** rather than a plausible guess, and is the second of only two windowless vendors (OYO is the other, for a different reason: it routes through Arena). A guessed cutoff is worse than a blank, because the engine would hand a manager a deadline that may not exist. The catalog tracks this as outstanding work in a test, not a comment.
- **All keg vendors** — empty-keg return count is a required field before a delivery can be marked received.
- **Staple kegs vs. rotating kegs** — the draft program is two different problems wearing one label, and they need opposite treatment.

  A **staple** is a keg invoiced in **two or more separate orders** inside the sampled window. Of **35 distinct keg products** over 2026-08-28..09-28, **15** meet that bar — but only **13** are genuine staples. The other two are why the rule needs judgement, and both are covered below. These thirteen have a real trailing baseline and are forecast normally:

  | Keg | Vendor | Size | Rate | $/keg |
  |---|---|---|---|---|
  | Downeast Original Cider | Superior | 1/2 bbl | 2.5 / wk | $194.00 |
  | Bellafina Secco Frizzante | Heidelberg | 1/6 bbl | 2.0 / wk | $150.00 |
  | Garage Beer Lime | Superior | 1/2 bbl | 0.9 / wk | $135.00 |
  | Busch Light Draft | Columbus Dist. | 1/2 bbl | 0.9 / wk | $126.00 |
  | Columbus Brewing Company Bodhi | Superior | **50 L** | 0.7 / wk | $197.00 |
  | Miller High Life | Superior | 1/2 bbl | 0.7 / wk | $115.00 |
  | Fat Head's Bumble Berry | Cavalier | 1/2 bbl | 0.7 / wk | $169.99 |
  | Golden Road Mango Cart | Columbus Dist. | 1/2 bbl | 0.7 / wk | $150.00 |
  | Rhinegeist Cincy Light Lager | Superior | 1/2 bbl | 0.7 / wk | $130.00 |
  | Sierra Nevada Hazy Little Thing | Superior | 1/2 bbl | 0.5 / wk | $191.00 |
  | Dogfish Head 30 Minute Light IPA | Superior | 1/2 bbl | 0.5 / wk | $187.00 |
  | BrewDog Elvis Juice IPA | Superior | 1/2 bbl | 0.5 / wk | $185.00 |
  | Real American Light Lager | Heidelberg | 1/2 bbl | 0.5 / wk | $120.00 |

  The remaining **20 keg products were each bought exactly once** — that is the **rotating** program, and it must be excluded from baseline learning entirely. A one-off keg has a trailing average of "1", which is indistinguishable from a slow staple and will be reordered forever if the engine does not know the difference.

  Four consequences for the build:

  1. **A repeating keg is not automatically a staple.** Immigrant Son Gourdians Pumpkin Ale repeated (8/26 and 9/2, Sixth City, 1/6 bbl) because it was September. Seasonal kegs repeat *inside* their season and then vanish, so repetition alone is not the test — `season` has to gate it, the same failure mode as the seasonal cocktail launches.
  2. **A repeat can also be a mapping artifact.** *Butcher And The Brewer: Albino Stout* shows two orders, but they are **two different beers**: item 1555 (Albino Stout) and item 1871 (Nitro Albino Stout), which MarginEdge collapses onto one product name. Counted by product it looks like a repeating line; counted by item code it is two one-offs. **The staple test has to run on vendor item codes, not product names**, or a rotating vendor's near-duplicates will manufacture phantom staples.
  3. **Staples span five vendors and three cutoffs.** Nine sit on Superior's and Columbus Dist.'s Sunday 7 PM, two on Monday 5 PM (Cavalier, and Sixth City for the rotation), and **Bellafina alone sits on Heidelberg's Wednesday 5 PM** — at 2 sixth-barrels a week it is the second-largest keg line by spend and the only one with no second chance inside the week.
  4. **Keg formats are not just halves and sixths.** Bodhi ships **50 L** and Athletic Wild Run NA ships **1/4 bbl**; the catalog now carries `fifty_liter`, `quarter_barrel` and `twenty_liter` yields (1,603 / 941 / 641 oz, on the same net-of-foam basis as the original two). Before this a 50 L staple could not be sized at all.
- **Product names must be the full vendor name, not floor shorthand.** The first version of the guide listed kegs as "Dogfish", "CBC", "Cheetah" and "Hazy Jane Hug". Auditing against MarginEdge showed shorthand hides real errors: "CBC" is *Columbus Brewing Company Bodhi* (a 3x staple that a name-based keg audit missed entirely, because the shorthand contains no keg token), Superior carries **seven** different Dogfish kegs so "Dogfish" is ambiguous, and "Hazy Jane Hug" had **fused two different beers** — BrewDog Hazy Jane (Superior, 1/6 bbl) and Goose Island Hazy Beer Hug (Columbus Dist., 1/2 bbl). Neither was what was actually purchased. Every catalog line carries the MarginEdge product name and item code.

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
| Empty kegs returned vs. deposits charged — **Superior** | 84 / 117 (72%) over the 2026-06-30..09-22 quarter | Above 95% |
| Empty kegs returned vs. deposits charged — **Columbus Dist.** | 36 / 34 (106%) over the same quarter | Hold above 95% |
| Outstanding keg deposit float | **$990 at Superior**, &minus;$60 at Columbus Dist. | Under $200 per vendor |
| Kegs delivered with no deposit line charged | 7 of 76 (9%) in the sampled month | Under 2% |
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
17. **Does Cavalier's "1/6 bbl only" rule still hold?** Fat Head's Bumble Berry is carried as a **1/2 bbl** — confirmed by purchasing, 3 units at $169.99 in the 2026-07-20..08-28 window — which contradicts the standing rule in the order guide. Either the rule has exceptions or it is stale. The catalog currently models the product as it is actually bought.
18. ~~What is Pamplemousse?~~ **Resolved: a 750ml liqueur bottle from Arena only** (an earlier draft wrongly had it on Cavalier). It appears nowhere in the purchase report, so there is no observed cost or depletion rate, and `pack_size` assumes Arena sells by the bottle rather than the case.
19. ~~**What is Berardi's exact Sunday cutoff time?**~~ **Resolved 2026-09-29: Sunday by 5:00 PM**, confirmed by the operator. Catalog updated from the 19:00 placeholder to 17:00, which puts Berardi's on the same cutoff as Arena, two hours ahead of Superior and Columbus Dist.
20. ~~**Which delivery days are vendor-stated vs. merely observed?**~~ **Partly resolved 2026-09-29.** The catalog and guide now carry the *observed* days, because MarginEdge invoice dates beat a written guide nobody had reconciled: Superior and Columbus Dist. moved Mon→Tue, Sixth City to Wed, Arena to Thu. Order days are operator-confirmed and are the firm half of the schedule.

    **A sample-size lesson worth keeping.** The first pass read Arena's delivery day off a single month (13 invoices) and concluded "Thu/Fri, never Monday". Pulling the full quarter — 45 invoices — changed the answer: **2 of 45 did land on a Monday**, and the day that actually matters is clear only when weighted by money. Thursday is 11 invoices but **$54,488, 60% of all Arena spend**, averaging $4,953 a drop; Saturday is the most *frequent* day at 13 invoices and just **5.7% of spend**. Counting invoices gives Saturday; counting dollars gives Thursday. **A month is not enough to read a weekday pattern, and unweighted counts mislead when invoice sizes differ by 10x.** Both rules now apply to every vendor in the appendix.

    **Superior and Columbus Distributing are now settled beyond argument.** Expanding their full quarter (45 invoices, 2026-06-30..09-22) gives **Columbus Dist. Tuesday on 25 of 25 invoices** and **Superior Tuesday 11 / Friday 9 and nothing else** — precisely the two order windows, both in regular use. Where a vendor runs a route, the invoice dates say so immediately; Arena's scatter across six weekdays was the exception, not the norm.

  **The sample-size lesson has now cost real accuracy twice, so it is a build requirement, not an anecdote.** Rebuilding the keg rates on the quarter changed two of them materially: **Garage Beer Lime is 1.67/week, not 0.90** (20 kegs across 11 of 12 weeks — it was carried at half its real rate), and **Busch Light Draft is not a staple at all** — bought exactly twice, on 2026-09-15 and 09-22. The one-month sample happened to be precisely the window it launched in, so a brand-new line read as an established staple. The engine therefore needs three things: **a minimum history before a line earns a rate**, **an explicit "new line, insufficient history" state** rather than a confident wrong number, and **a stopped-line prompt** — Michelob Ultra Superior Light keg ran 12 kegs across five straight weeks and then vanished for two months. The operator confirmed that one was a deliberate short run, so there is nothing to chase; the point is that **a deliberate limited run and a line that silently fell off the order are indistinguishable in the invoice data**. The engine cannot tell them apart, so when a line goes quiet it must *ask* rather than either re-ordering it or dropping it.

  **Still open:** no rep has confirmed a delivery day in writing.
21. ~~What is Arena's order day?~~ **Resolved: Sunday and Wednesday, confirmed 2026-09-28.** All nine vendors now have operator-confirmed order days. Arena's *delivery* days remain open — see question 20 — and matter disproportionately because Arena is the largest beverage vendor at roughly $37.3K/month, over half of beverage spend.
22. **What is the fall/winter brief for the rotating keg lines?** The standing instruction to Sixth City and Cavalier is "summer: sours, smoothies, pale ales," which is now wrong. Purchasing shows the fall rotation already arriving — pumpkin, caramel apple cider, bourbon barrel ale, porter — but the written brief has not been updated.
23. ~~**What is Amazon's order window?**~~ **Resolved 2026-09-29, but not the way the question assumed.** There is no vendor cutoff to discover: Amazon is self-service with 1–2 day delivery, so the window is a **policy we set**, not a deadline imposed on us. The measured problem is different from the one asked about — over 2026-06-29..09-28, **195 orders landed on only 56 separate days** (3.5 orders per ordering day; eight in one day happened four times), and **60 of 195 orders were under $50**, together worth $1,535, or 5.6% of spend. Nothing is batched.

    Policy adopted: **batch to Monday and Thursday**, which were already the two heaviest days (44 and 38 orders), so it formalises existing behaviour rather than fighting it. Two orders a week instead of fifteen is roughly **85% fewer receiving events** for the same product. One documented exception: a genuine 86 mid-service bypasses the batch, so nobody has a reason to hide an order.

    **Still open:** who owns pressing the button, and whether the Thursday batch is needed every week or only in event weeks.

24. ~~**What is Hillcrest's order window?**~~ **Resolved 2026-09-29 on the delivery side, still open on the cutoff hour.** Hillcrest is the largest supplier in the building at **$159,381 across 61 orders** in the quarter, and it runs **two accounts on two different schedules**: **71357** (food and broadline, $132,436) lands **Monday and Friday**; **71361** (paper, disposables, chemicals, $27K) lands **Tuesday and Friday**. Friday alone carries **$82K of the $159K**, and is the one cutoff both accounts share — making Thursday the most expensive deadline in the building to miss. Nothing has ever landed on a Sunday, and one invoice in three months fell on a Thursday.

    ~~What the data cannot give us is the cutoff time.~~ **Resolved 2026-09-29: 4:00 PM, day before delivery, both accounts**, confirmed by the operator. All three Hillcrest windows now carry `order_time: "16:00"` and no longer flag for confirmation. Worth recording why the data could never have supplied it: MarginEdge stores only the invoice, and its `createdDate` is always *exactly one day after* the invoice date — 61 times out of 61 — so it reflects invoice processing, not ordering. **Some schedule facts are only obtainable from a person, and the engine should mark those fields as human-sourced rather than leaving them to look derivable.** One consequence for the floor: Hillcrest's Thursday 4 PM sits an hour before Hartzler's Thursday 5 PM, so Thursday afternoon carries two cutoffs back to back.

    Two findings worth acting on regardless: the bar draws on **both** accounts (prep pantry on 71357, bevnaps/straws/Beer Clean glass wash on 71361), and **allulose 38006 at $214.08 plus frozen strawberries 115005 are each being ordered on both accounts** — the same item on two delivery days, which is how a duplicate tub arrives. Each item needs assigning to one account.
25. **The allulose is a powder — so what does the recipe mean?** Confirmed from the vendor item name itself: Hillcrest code 38006, "Sugar Allulose Powder Organic". SS-1 asks for 34 **fluid ounces** of cold allulose, a volume measure against a powder. This is now a recipe question rather than a sourcing one: either the spec means a liquid allulose nobody buys, or it means powder and the figure should be a weight. Scarlett Spritz cannot be batched or costed until it is decided, and the two must not be silently converted.
27. **What is Buckeye Beverage’s order cutoff?** The only schedule fact in the catalog that is a genuine blank rather than a placeholder. Monday delivery is unambiguous — 12 of 17 invoices, ~82% of spend, a Monday invoice in every week of the quarter — but no cutoff has ever been recorded and MarginEdge cannot supply one, since it stores the invoice rather than the order. This is the same class as the Hillcrest cutoff: **only a person can answer it.** Until someone asks the rep, Buckeye carries no window and the engine cannot recommend an order for the fountain, the BIB mixers, the bar juices or the draft gas. **One phone call closes this.**

28. **What does the STA program actually buy, and who is auditing the zero-cost lines?** $621 of Buckeye’s $7,789 is not product: the `901` "STA-Full Program" service fee is $51.75 on 7 invoices as a line plus $258.75 more as an invoice-level charge, and delivery adds $96. Separately, the CO2 and nitrogen cylinders bill at **$0.00**. Both halves are invisible to a spend-based review — the fee because nobody reads charge fields, the gas because it costs nothing — and the gas is what stops the draft system. Worth one look at what the program includes.

29. ~~**What is the bitters pack size?**~~ **Still open, and now quantified.** The 2026-08-14 Southern Glazer’s invoice carries `334995` Angostura Bitters and `976180` Angostura Orange, **each at quantity 1 for $182.30**, $364.60 together. At that unit price a "unit" is a case, not a bottle — Angostura 4oz retails around $9. Because it is a once-a-quarter buy nobody notices, but the unit is wrong in inventory until it is fixed, and every depletion rate built on it will be wrong by the pack factor. **Confirm the case count with Bethany.**

30. **Which of the two Heidelberg duplicate invoices gets credited, and by whom?** $365.89 across two pairs on 12–13 August, confirmed by identical line items at identical unit prices. Smaller than the Arena double bill but the same failure: **nothing in MarginEdge flagged either.** Arena’s $5,781.06 was confirmed by the operator and is recoverable; these two have not been raised with Tess. **Needs an owner for chasing vendor credits generally**, or the detection produces findings nobody acts on.

26. **What is on the fall/winter cocktail menu?** Not yet handed over. The seasonal section of the guide holds a deliberately empty list rather than a guessed one; nothing can be ordered or forecast for these until the specs exist.

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

Seed data for the scheduling engine. **Order days are operator-confirmed (2026-09-28/29). Delivery days are observed from MarginEdge invoice dates over 2026-08-28..09-28**, and where the two disagreed the invoices won — `TH_ORDER_GUIDE.docx` had several delivery days that a month of real receiving never once showed. No rep has confirmed a delivery day in writing; see open question 20.

| Vendor | Order due | Delivers | Channel | Notes |
|---|---|---|---|---|
| Superior Beverage | Sun 7:00 PM | **Tue** | Phone — Shane (614) 306-4582 | Second window: **Wed 7:00 PM → Fri**. Docx said Mon; invoices say Tue |
| Hartzler Family Dairy | Thu 5:00 PM | Tue | **Email only** — orders@hartzlerdairy.com | Café. Five-day lead, the longest of any vendor |
| Berardi's Coffee | **Sun 5:00 PM** | Tue/Wed | **Email only** — orders@berardiscoffee.com | Café |
| Amazon | **Mon + Thu 5:00 PM** *(our policy)* | 1–2 days | Online | Long-tail prep goods. 65 orders/mo. No vendor cutoff exists — see below |
| Hillcrest Foodservice — acct **71357** | **Sun + Thu, 4:00 PM** | **Mon** + Fri | Phone | Food/broadline. $132K/quarter |
| Hillcrest Foodservice — acct **71361** | **Mon + Thu, 4:00 PM** | **Tue** + Fri | Phone | Paper, disposables, chemicals, bar consumables. $27K/quarter |
| The Columbus Dist. Co. | Sun 7:00 PM | **Tue** | Phone — Conner (937) 581-1234 | Docx said Mon; every invoice landed Tue |
| Arena Liquor | Sun 5:00 PM | **Thu** | **Email only** — arenaliquor@gmail.com | Second window: Wed 9:00 PM → Thu. Thursday carries **60% of Arena spend** across a 45-invoice quarter. Largest beverage vendor |
| Southern Glazer's of OH | Mon 4:00 PM | Tue | Phone — Bethany (740) 507-1973 | Wed follow-up → Fri, **used 6 of 20 invoices** — a real second slot, still confirm first |
| Sixth City Distributors | Mon 5:00 PM | **Wed** | Phone — Jenna Carelly (614) 301-4877 | Rotating 1/6 bbl only. Neither source said Wed; invoices do |
| Cavalier Distributing | Mon 5:00 PM | Tue | Phone — Dan (614) 582-0014 | Rotating 1/6 bbl, **plus named SKUs** |
| Heidelberg / Wine Trends | Wed 5:00 PM | **Thu PM** | Phone — Tess Canby (740) 583-4555 | Deliver after 9am, hallway behind bar. **Moved Tue → Thu on 1 Sep 2026**; across the whole quarter it misreads as a Tue+Thu route |
| **Buckeye Beverage** | **Not known — ask the rep** | **Mon** | Phone — acct 50668 | **Fountain, all BIB mixers, bar juices, and the CO2 + nitrogen for the draft system.** $7,789/quarter. Absent from this guide until 29 Sep 2026 |
| OYO Vodka | As needed | As needed | Phone — Zack (614) 981-9341 | **Order through Arena first.** No window — routes through Arena |

**Tuesday takes six** (Superior, Columbus Dist., Berardi’s, Southern Glazer’s, Cavalier, Hartzler), so receiving is the constraint on Tuesday morning, not ordering. **Monday now takes two** — Hillcrest’s food account and Buckeye. An earlier draft of this appendix said "Monday takes no delivery at all" while its own table already showed Hillcrest 71357 landing Monday; adding Buckeye made the claim doubly wrong. **Thursday afternoon carries two cutoffs an hour apart** — Hillcrest 4 PM (both accounts) and Hartzler 5 PM — and Thursday is also the heaviest receiving day, taking Heidelberg’s delivery since 1 Sep plus 60% of Arena’s spend. Heidelberg’s own cutoff is the day before, **Wednesday 5 PM**, alongside Superior’s Wednesday 7 PM and Arena’s Wednesday 9 PM.

**Two vendors carry no order window**, for two different reasons. OYO has no cutoff of its own because it routes through Arena. **Buckeye has a certain delivery day and an unknown cutoff**, and carries a blank rather than a guess — handing a manager a deadline that may not exist is worse than handing them nothing. See open question 27.
