# Superior Beverage & Columbus Distributing - every product, 2026-06-30 to 2026-09-22

Pulled from the MarginEdge API on 2026-09-29. All **45 invoices** expanded to
line-item detail: Superior (vendor `148730`) 20 invoices, Columbus Distributing
(vendor `147386`) 25 invoices. A 12.00-week window exactly.

Both reconcile to the penny, which is the check that makes everything below usable:

| | Superior | Columbus Dist. |
|---|---|---|
| Invoices | 20 | 25 |
| Line items | 197 (9 zero-qty placeholders) | 131 (1 placeholder) |
| Distinct item codes | **25** | **15** |
| Product lines | $24,215.51 | $17,992.69 |
| Keg deposit lines | $990.00 | &minus;$60.00 |
| Delivery | $30.00 | &mdash; |
| Credits | &minus;$324.00 | &mdash; |
| **Invoice totals** | **$24,911.51** | **$17,932.69** |
| Reconciliation gap | **$0.00** | **$0.00** |

## The delivery days are now settled beyond argument

- **Columbus Distributing: Tuesday, 25 out of 25 invoices.** No exceptions in a quarter.
- **Superior: Tuesday 11, Friday 9, nothing else.** Exactly the two order windows
  (Sunday 7pm &rarr; Tuesday, Wednesday 7pm &rarr; Friday). Both are used, roughly evenly.

This is what a real schedule looks like in the data, and it is worth contrasting
with Arena, where 45 invoices scattered across six weekdays. Where a vendor has a
route, the invoice dates say so immediately.

## Superior Beverage - 25 items

| # | Code | Product | Qty | Orders | Spend | Price |
|---|---|---|---|---|---|---|
| 1 | `11488` | 1 Down Cider Original 1/2K | 29 | 12 | $5,626.00 | $194.00 |
| 2 | `01500` | Miller Lite 1/24 12 Fl Oz Bottle | 130 | 10 | $2,702.70 | $20.79 |
| 3 | `15305` | Garage Lime 1/2 Bbl | 20 | 11 | $2,700.00 | $135.00 |
| 4 | `26240` | Sun Cruiser CS 12oz Class Tea 24PK LSE | 47 | 10 | $1,833.00 | $39.00 |
| 5 | `10051` | Columbus Bodhi  50 Liter | 9 | 8 | $1,773.00 | $197.00 |
| 6 | `17076` | Rhine Cincy Li 1/2 Bbl | 10 | 9 | $1,300.00 | $130.00 |
| 7 | `11844` | Brewdog Elvis Juice 1/2 Bbl 1/1 15.5 Gal Keg | 7 | 7 | $1,295.00 | $185.00 |
| 8 | `01025` | Miller HL | 10 | 6 | $1,150.00 | $115.00 |
| 9 | `17044` | Dog 30 Minute Light 1/2 Bbl | 5 | 4 | $935.00 | $187.00 |
| 10 | `67218` | Sier Hazy Litt 1/2BBL | 4 | 4 | $764.00 | $191.00 |
| 11 | `03000` | Coors Banquet Stubby 2/12 12 Oz Bottle | 30 | 11 | $671.70 | $22.39 |
| 12 | `01625` | Pabst Blue Ribbon 1/2 Bbl 1/1 15.5 Gal Keg | 5 | 2 | $565.00 | $113.00 |
| 13 | `06026` | Sa Cherry Wht  1/2 Bbl | 2 | 2 | $374.00 | $187.00 |
| 14 | `06025` | Sa Lager  1/2 Bbl | 2 | 2 | $374.00 | $187.00 |
| 15 | `16383` | Ath Run Wild N/a 1/4 Bbl | 3 | 3 | $283.50 | $94.50 |
| 16 | `14668_Down` | Down Donut | 1 | 1 | $204.00 | $204.00 |
| 17 | `14668` | Down Cider  Donut 1/2k | 1 | 1 | $204.00 | $204.00 |
| 18 | `01549` | Miller Lite 2/12 12 Fl Oz Bottle | 9 | 1 | $201.51 | $22.39 |
| 19 | `01558` | Miller Lite 1/18 12 Fl Oz Bottle | 12 | 1 | $191.88 | $15.99 |
| 20 | `06095` | Samuel Adams Octoberfest 1/2 Bbl 1/1 15.5 Gal Keg | 1 | 1 | $187.00 | $187.00 |
| 21 | `12229` | Brew Hazy Jane  1/6 Bbl | 2 | 2 | $186.00 | $93.00 |
| 22 | `14472` | Down Cider Blackberry 1/6k | 2 | 2 | $184.00 | $92.00 |
| 23 | `06034` | Sa Octoberfest  1/6 Bbl | 2 | 2 | $184.00 | $92.00 |
| 24 | `14161` | Brew Af Mix N/a 2/12 Pk Can | 6 | 5 | $182.34 | $30.39 |
| 25 | `26092` | Mamitas--cs 12oz Pineap 6/4 Pk  Case | 3 | 2 | $143.88 | $47.96 |

**Downeast Original cider is Superior's biggest line by a distance** - 29 half-barrels
across 12 of the 12 possible weeks, $5,626, or 23% of everything Superior sells us.

## Columbus Distributing - 15 items

| # | Code | Product | Qty | Orders | Spend | Price |
|---|---|---|---|---|---|---|
| 1 | `07304` | Ultra Gold 12 NR | 247 | 11 | $6,320.73 | $25.59 |
| 2 | `01753` | Surfside Lemonloose | 91 | 11 | $3,548.09 | $38.99 |
| 3 | `06792` | Michelob Ultra Superior Light 1/1 15.5 Gal Keg | 12 | 5 | $1,620.00 | $135.00 |
| 4 | `1649` | Gi Hazy Hug "1/2 | 9 | 7 | $1,350.00 | $150.00 |
| 5 | `73592` | Gr Mgo Df   1/2 Keg | 8 | 7 | $1,200.00 | $150.00 |
| 6 | `02501` | Bl Big Blue | 37 | 10 | $769.23 | $20.79 |
| 7 | `02244` | Superlyte Limeloose | 16 | 6 | $623.84 | $38.99 |
| 8 | `07892` | Busch Lt Df   '1/2 | 4 | 2 | $504.00 | $126.00 |
| 9 | `01627` | Surfside Lemonade Vodka 6/4 12 Fl Oz Can 9pf | 10 | 1 | $450.00 | $45.00 |
| 10 | `02242` | Superlyte Blueloose | 11 | 4 | $428.89 | $38.99 |
| 11 | `01484` | Nutrl Bl Chry 6/4can | 9 | 3 | $388.53 | $43.17 |
| 12 | `02243` | Superlyte Orngloose | 9 | 2 | $350.91 | $38.99 |
| 13 | `02246` | Superlyte Vp  3/8/12oz | 6 | 2 | $256.50 | $42.75 |
| 14 | `02245` | Superlyte Pnchloose | 3 | 3 | $116.97 | $38.99 |
| 15 | `26595` | Kona Bwave Df '1/6 | 1 | 1 | $65.00 | $65.00 |

**Columbus Distributing is a narrow, high-volume account.** Fifteen items, and
Michelob Ultra Gold alone is 247 cases and $6,321 - 35% of the account. Add
Surfside hard lemonade and the top two are 55%. There is almost no tail here: the
five Superlyte flavour codes (`02242`-`02246`) are one variety programme, not five
separate decisions.


## Four things to act on

### 1. $990 of keg deposits is outstanding at Superior, and the balance is drifting

Over the quarter Superior charged **117 keg deposits** and credited back **84** -
a gap of **33 kegs, $990**. Tracing it invoice by invoice shows this is not noise,
it is drift:

```
  Jun 30 .. Jul 21    running balance hovers at -2 to +3   (healthy)
  Jul 28 .. Aug 21    climbs +4 -> +11 -> +17 -> +25
  Sep 01 .. Sep 22    +30 -> +27 -> +34 -> +33
```
Two invoices did the damage: **2026-08-21, six kegs bought and none returned**, and
**2026-09-18, seven bought and none returned**. On both dates the driver left with
nothing.

**This revises what I told you earlier.** Reading one month (2026-08-28..09-28)
across all beverage vendors, deposits looked balanced - 69 paid against 66
returned, a $90 float - and I reported that returns were working. Superior alone
over that same month is 39 paid / 31 returned, which still looks close to fine. The
drift is only visible over a quarter, because **an unreturned keg does not come back
as a negative later - it just stops appearing.** A one-month window cannot see a
slow leak; it only sees the current week's exchange.

Columbus Distributing is the opposite and needs no action: **34 paid, 36 returned**,
a $60 credit, meaning they collected two empties from an earlier period. That is
what a working return loop looks like.

For context: 33 kegs outstanding is **more than the tap count**, so this is not all
beer currently pouring. Ask Superior for a keg-balance statement and reconcile it
against what is physically in the cooler.

### 2. The guide's Staple Kegs rates were built on one month and two are wrong

| Keg | Guide said (1 month) | Quarter actual | |
|---|---|---|---|
| Garage Beer Lime | 0.9 / wk | **1.67 / wk** | understated by nearly half |
| Busch Light Draft | 0.9 / wk | **0.33 / wk** | overstated 3x |
| Downeast Original | 2.5 / wk | 2.42 / wk | correct |
| Miller High Life | 0.7 / wk | 0.83 / wk | close |
| Rhinegeist Cincy Light | 0.7 / wk | 0.83 / wk | close |
| CBC Bodhi 50L | 0.7 / wk | 0.75 / wk | correct |
| BrewDog Elvis Juice | 0.5 / wk | 0.58 / wk | correct |
| Dogfish 30 Minute | 0.5 / wk | 0.42 / wk | close |
| Sierra Hazy Little Thing | 0.5 / wk | 0.33 / wk | overstated |
| Golden Road Mango | 0.7 / wk | 0.67 / wk | correct |

**Busch Light Draft is not a staple at all.** It has been bought exactly twice -
2026-09-15 and 2026-09-22, two kegs each. It is a brand-new line that started in
September, and the one-month sample happened to be precisely the window it launched
in, so a launch read as an established 0.9/wk staple. **Garage Beer Lime is the
opposite**: 20 kegs across 11 of 12 weeks, the second most consistent keg in the
building, and the guide had it at half its real rate.

### 3. The Michelob Ultra keg was a deliberate short run

**Michelob Ultra Superior Light keg** (Columbus Dist. `06792`, $135) was bought
**12 kegs across 5 consecutive weeks** - 6/30, 7/7, 7/14, 7/21, 7/28 - and then
**never again**. Two full months of silence. $1,620 of keg, running weekly, stopped
dead.

**Confirmed by the operator 2026-09-29: this was intentional, a short run only.**
So there is nothing to chase - but it is worth keeping on the record, because a
deliberate limited run and a line that silently fell off the order **look
identical in the invoice data**: weekly and confident, then nothing. The engine
cannot tell them apart, which means when a line goes quiet it has to **ask**
rather than either re-order it or drop it. Michelob Ultra is the benign case;
the same shape with nobody's intent behind it is a hole in the tap list.

### 4. Miller Lite is ordered in three different pack sizes under one product

Superior bills Miller Lite on three codes that MarginEdge maps onto a single product:

| Code | Pack | Price | Qty |
|---|---|---|---|
| `01500` | 1/24 12oz bottle | $20.79 | 130 |
| `01549` | 2/12 12oz bottle | $22.39 | 9 |
| `01558` | 1/18 12oz bottle | $15.99 | 12 |

Product-level quantity reads **151 units** of Miller Lite, which is 130 24-packs
plus 9 12-packs plus 12 18-packs - three different bottle counts added together.
Same failure as Arena's L/B codes, different vendor, so this is systemic to how
MarginEdge maps vendor items: **depletion has to be keyed on the item code.**

One outright duplicate as well: **`14668` "Down Cider Donut 1/2k" and `14668_Down`
"Down Donut"**, both $204, one keg each, filed under *different* MarginEdge product
ids. Because the ids differ, a product-level duplicate check will not catch it -
only the shared `14668` base code gives it away.

For the record, two things that look like duplicates and are not: the five
**Superlyte** flavour codes (`02242`-`02246`) are genuinely different flavours that
happen to share a $38.99 price, and **Sam Adams Cherry Wheat** (`06026`) beside
**Sam Adams Lager** (`06025`) are two beers at the same $187. A same-price check
alone would flag both wrongly.

