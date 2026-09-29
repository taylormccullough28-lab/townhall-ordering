# Buckeye Beverage, Heidelberg & Southern Glazer's - every product, 2026-06-29 to 2026-09-24

Pulled from the MarginEdge API on 2026-09-29. **79 invoices** expanded to line-item
detail. All three reconcile to the penny:

| | Buckeye | Heidelberg | Southern Glazer's |
|---|---|---|---|
| Vendor id | `147339` | `120257` | `147393` |
| Invoices | 17 | 42 | 20 |
| Item codes | **19** | **49** | **24** |
| Product lines | $7,072.08 | $18,762.17 | $20,321.05 |
| Fees / deposits / splits | $362.25 | $69.00 | &mdash; |
| Other charges | $258.75 | $361.00 | &mdash; |
| Delivery | $96.00 | &mdash; | &mdash; |
| Credits | &mdash; | &minus;$91.00 | &mdash; |
| **Invoice totals** | **$7,789.08** | **$19,101.17** | **$20,321.05** |
| Gap | **$0.00** | **$0.00** | **$0.00** |

## The headline: Buckeye Beverage was missing from the guide entirely

It is the **fountain, BIB and gas vendor** - 19 items, all of them bar- or
cafe-critical, and none of it was in the guide, the catalog, the contacts or the
PRD. It never surfaced because the vendor list came from `TH_ORDER_GUIDE.docx` and
was then only sanity-checked against a top-12-by-spend ranking, where Buckeye sits
13th. Ranking inside an already-narrowed list cannot find what the list omitted.

**Monday is the day: 12 of 17 invoices and $6,377 of $7,789 (82%).** Every single
week in the quarter has a Monday invoice, without exception.

| # | Code | Item | Qty | Orders | Spend |
|---|---|---|---|---|---|
| 1 | `100` | Coca-Cola 5 GAL | 9 | 9 | $1,285.02 |
| 2 | `101` | Diet Coke 5GAL | 8 | 8 | $1,142.24 |
| 3 | `1011` | Nitrogen Large | 13 | 12 | $798.85 |
| 4 | `128` | Sprite 2.5 | 10 | 10 | $776.70 |
| 5 | `653` | Cranberry 20% 3 BIB | 7 | 7 | $601.37 |
| 6 | `297` | Whiskey Sour 3 Bib | 10 | 10 | $580.00 |
| 7 | `232` | Pink Lemonade 3 Gal | 7 | 7 | $432.88 |
| 8 | `269` | Pineapple 8 Ltr | 4 | 4 | $320.00 |
| 9 | `249` | Craft 62 Ginger Beer 3 GAL | 4 | 4 | $294.20 |
| 10 | `650` | Orange Juice 100% 8L | 2 | 2 | $166.00 |
| 11 | `247` | Craft 62 Ginger Ale 3 Gal | 2 | 2 | $147.10 |
| 12 | `246` | Craft 62 Cream Soda 3 GAL | 2 | 2 | $147.10 |
| 13 | `223` | Ginger Ale | 2 | 2 | $123.68 |
| 14 | `244` | Craft 62 Black Cherry 3 Gal | 1 | 1 | $73.55 |
| 15 | `248` | Craft 62 Lemon-Line 3 Gal | 1 | 1 | $73.55 |
| 16 | `233` | Yellow Lemonade 3 Gal | 1 | 1 | $61.84 |
| 17 | `277` | Tonic 8L | 1 | 1 | $48.00 |
| 18 | `1003` | 20# Pop | 1 | 1 | $0.00 |
| 19 | `1010` | 50# Beer | 2 | 1 | $0.00 |

Things on that list that matter more than their price suggests:

- **`1003` 20# Pop and `1010` 50# Beer are CO2 cylinders** - the gas for the
  fountain and the draft system. They bill at **no charge** under the STA program,
  which is exactly why they are easy to forget until the beer stops pouring.
- **`653` Cranberry 20% BIB** - this answers the open question from the fall prep
  sheet, which called for organic cranberry juice and noted "you buy a cranberry
  BIB" without a source. The source is Buckeye. Whether a 20% BIB satisfies
  "organic" is still a recipe question.
- **`297` Whiskey Sour BIB** - ten of seventeen invoices, the most consistently
  ordered item on the account.
- **`277` Tonic 8L** and **`1011` Nitrogen Large** - gin and tonics, and nitro.
- **`269` Pineapple 8L** maps to the same MarginEdge product as Hillcrest's
  `50001` Juice Pure Pineapple, so pineapple juice is **dual-sourced** and will
  double-count unless the engine keys on item code.
- **`901` STA-Full Program** at $51.75 on 7 invoices, plus $258.75 booked as an
  invoice-level charge under the same name: a recurring service fee, not product.


## Heidelberg changed delivery day on 1 September, and the quarter average hides it

Pooled over the quarter Heidelberg looks like **Tuesday 19 / Thursday 16**, which
reads as a two-day-a-week vendor. Broken out by week it is nothing of the kind:

| ISO week | Dates | Days invoiced |
|---|---|---|
| 27&ndash;35 | 30 Jun &ndash; 31 Aug | **Tuesday, every week without exception** |
| 36&ndash;39 | 1 Sep &ndash; 24 Sep | **Thursday, every week, no Tuesdays at all** |

Heidelberg **moved from Tuesday to Thursday at the start of September**. The
Thursday pattern is the current one, so the guide's "Wed 5 PM &rarr; Thu" is right
*now* and was wrong for the first two thirds of the quarter. The handful of Wed and
Fri invoices are catch-ups around the switch.

**This is the opposite failure to the one a short window causes**, and worth
stating plainly because the two are easy to confuse:

- A **one-month** window made Busch Light Draft look like an established staple
  when it was a September launch.
- A **one-quarter** window makes Heidelberg look like a Tue+Thu vendor when it is
  a Tue vendor that became a Thu vendor.

Neither window length is safely "enough". **The engine has to look for a regime
change, not just average a longer period** - a vendor whose weekday distribution is
bimodal over time is either a two-day vendor or a vendor that moved, and those need
opposite treatment. Checking whether the two modes overlap in time separates them.

### Heidelberg - 49 item codes

| # | Code | Item | Qty | Orders | Spend |
|---|---|---|---|---|---|
| 1 | `101613` | Vinos Atlantic 750ml Ethos Blanc De | 53 | 13 | $3,417.65 |
| 2 | `798003` | Bellafina 1/6bbl Secco Frizzante Keg | 9 | 2 | $1,350.00 |
| 3 | `94802` | Riedel Degustz 0489/0 Red | 16 | 4 | $1,056.00 |
| 4 | `891202` | Routestock Cabernet Sauvignon Napa 1/12 750 Ml Bottle | 51 | 9 | $1,033.45 |
| 5 | `911100` | Frenzy Sauvignon Blanc 1/12 750 Ml Bottle | 6 | 6 | $783.70 |
| 6 | `16065` | Pacifico Clara 6/4 16 Oz Can | 23 | 9 | $772.11 |
| 7 | `968200` | Peyrassol La Croix Des Templiers Rose 1/12 750 Ml Bottle | 29 | 10 | $747.72 |
| 8 | `831713` | Catena Appell 750ml White Clay | 17 | 7 | $649.95 |
| 9 | `454080` | Chinola 750ml Passion Fruit L Iqueur | 5 | 5 | $629.80 |
| 10 | `12175` | Real Ameri Dft 1/2bbl Light Lager | 5 | 6 | $600.00 |
| 11 | `757601` | Vinos Atlantic 750ml Gordo | 23 | 6 | $569.97 |
| 12 | `769406` | De Loach Chardonnay Russian River Valley 1/12 750 Ml Bottle | 23 | 4 | $566.69 |
| 13 | `723600` | Union Sacre 750ml Riesling Dry | 41 | 8 | $546.53 |
| 14 | `60914` | Once Upon A Coconut Pure Coconut Water | 10 | 7 | $499.90 |
| 15 | `918018` | 750ml  Long Meadow Rc Sauv Blanc Nap | 12 | 4 | $459.84 |
| 16 | `100097` | Vinos Atlantic 1l Patio Pounder N V | 20 | 5 | $363.78 |
| 17 | `111802` | Count Karolyi 750ml Gruner Veltline | 35 | 6 | $350.00 |
| 18 | `848803` | Stella Pinot Grigio 1/12 750 Ml Bottle | 4 | 4 | $319.80 |
| 19 | `464045` | Mr. Boston 1L Peach Schnapps 12 | 18 | 8 | $311.34 |
| 20 | `385520` | Laurent Perrier Brut La Cuvee 1/6 750 Ml Bottle | 6 | 3 | $280.02 |
| 21 | `60910` | Once A Coconut Coco Watr 12pk | 14 | 12 | $272.87 |
| 22 | `267109` | Villard 750ml Syrah L'appel | 10 | 3 | $271.92 |
| 23 | `757154` | Ancient Peaks Zinfandel 1/12 750 Ml Bottle | 20 | 4 | $266.60 |
| 24 | `146010` | Maison Saleya Cotes De Provence Rose 1/12 750 Ml Bottle | 20 | 7 | $226.60 |
| 25 | `478900` | 750ml  Ch Grange Coch Morgon Charmes | 5 | 4 | $213.27 |
| 26 | `94807` | Riedel Degustz 0489/48 Champ | 3 | 1 | $198.00 |
| 27 | `557415` | 750ml  Mas Chevaliere Cab Pay D'oc 12 23 | 7 | 3 | $179.95 |
| 28 | `769402` | De Loach Chardonnay Heritage Reserve 1/12 750 Ml Bottle | 7 | 2 | $179.95 |
| 29 | `464010` | Mr Boston Triple Sec | 15 | 6 | $148.03 |
| 30 | `373403` | Ryans 1l Original Irish Cream | 1 | 1 | $135.00 |
| 31 | `793206` | Sokol Blosser Meditrina M 1/12 750 Ml Bottle | 1 | 1 | $119.95 |
| 32 | `16064` | Pacifico | 4 | 2 | $108.76 |
| 33 | `287901` | 750ml  Zilliken Riesling Estate | 9 | 3 | $108.00 |
| 34 | `968206` | Peyrassol Reserve Des Templiers 1/12 750 Ml Bottle | 6 | 1 | $103.98 |
| 35 | `224800` | Kris 750ml Pinot Grigio | 1 | 1 | $103.95 |
| 36 | `838719` | Hess Shirtail 750ml Sauv Blanc | 1 | 1 | $99.00 |
| 37 | `838709` | Hess Shirtail 750ml Chard Shirtail C | 1 | 1 | $99.00 |
| 38 | `838725` | Hess Select 750ml Pinot Gris | 1 | 1 | $95.95 |
| 39 | `327925` | 750ml  Nortico Alvarinho | 9 | 5 | $90.00 |
| 40 | `110243` | Chanteleuserie 750ml Rose Bourgueil | 6 | 1 | $79.98 |
| 41 | `848806` | Stella Montepulciano D Abruzzo 1/12 750 Ml Bottle | 1 | 3 | $79.95 |
| 42 | `146545` | Bollini 750ml Pinot Grigio | 6 | 1 | $75.96 |
| 43 | `185531` | Laurent Perrier Cuvee Rose Brut Wrap 1/12 750 Ml Bottle | 1 | 1 | $73.33 |
| 44 | `758663` | Villa Sandi 750ml Pinot Grigio | 6 | 1 | $47.94 |
| 45 | `991515` | Chateau Med 750ml Suduiraut Lions Se | 2 | 1 | $33.34 |
| 46 | `759201` | Frescobaldi 750ml Nipozzano Riser Va | 2 | 1 | $23.98 |
| 47 | `256098` | Louis Latour 750ml Ardeche Chard | 2 | 1 | $18.66 |
| 48 | `833704` | Excelsior 750ml Sauv Blanc | 0 | 1 | $0.00 |
| 49 | `910516` | Ch Des Jacques 750ml Moulin A Vent L | 0 | 1 | $0.00 |

Heidelberg is **the wine house**, and three things stand out. **Ethos Blanc de
Blanc (`101613`) is the single biggest line at $3,417.65 across 13 of 42 invoices**
- the house sparkling, and the most consistently reordered item on the account.
**Bellafina Secco keg (`798003`) is $1,350** and confirms the staple finding from
the keg work. And **$1,056 of it is not drink at all**: Riedel Degustation
glassware (`94802` red, `94807` champagne) at $66 a unit, 16 units over 4 invoices
- glass breakage, running through the wine vendor.

**Heidelberg also charges for splitting cases**, and it adds up: `00801` split-case
charges plus invoice-level "Split Case Charges" and "Service Fee" lines total
**$430** over the quarter. That is the cost of ordering wine by the bottle instead
of the case - worth knowing, and worth deciding deliberately rather than by
accident.

### Southern Glazer's - 24 item codes

| # | Code | Item | Qty | Orders | Spend |
|---|---|---|---|---|---|
| 1 | `0547649` | High Noon Cktl Vod - Selt Peac | 152 | 13 | $6,382.48 |
| 2 | `201010` | Red Bull Energy Drink | 67 | 12 | $2,994.00 |
| 3 | `951474` | Whitehaven Sauvignon Blanc Marlborough 1/12 750 Ml Bottle | 16 | 6 | $1,976.72 |
| 4 | `903751` | La Marca Prosecco Collezione Select 1/12 750 Ml Bottle | 16 | 7 | $1,392.00 |
| 5 | `557367` | Aperol Aperitivo 1/6 1 Ltr Bottle 22pf | 9 | 6 | $1,322.85 |
| 6 | `0409127` | Red Bull Energy Sugarfree Ca | 27 | 10 | $1,222.00 |
| 7 | `287189` | Whitehaven Sauvignon Blanc Marlborough 1/6 750 Ml Bottle | 13 | 5 | $936.00 |
| 8 | `694881` | Lucky One Vod Lemon Orig 24ls 355.000 Ml | 19 | 4 | $697.68 |
| 9 | `558752` | Llords Elderflower 30 1.000 Lt | 6 | 4 | $552.00 |
| 10 | `355642` | Veuve Clicquot Brut Cuvee Reserve 1/12 750 Ml Bottle | 1 | 1 | $456.00 |
| 11 | `617247` | Smith And Hook Proprietary Red Blend 1/12 750 Ml Bottle | 31 | 7 | $444.23 |
| 12 | `605512` | Hahn Pinot Noir 1/12 750 Ml Bottle | 40 | 9 | $440.00 |
| 13 | `595375` | Filthy Olive Brine 2/6 8 Oz Each | 6 | 5 | $287.70 |
| 14 | `976180` | Angostura Bitters Orange | 1 | 1 | $182.30 |
| 15 | `334995` | Angostura Bitters | 1 | 1 | $182.30 |
| 16 | `25213` | Dekuyper Peachtree Schnapps 1/12 1 Ltr Bottle 30pf | 1 | 1 | $144.40 |
| 17 | `332775` | Baileys Irish Cream 1/12 1 Ltr Bottle 34pf | 5 | 1 | $140.95 |
| 18 | `982819` | Red Bull Watermelon Red Can24p Foz | 3 | 1 | $138.00 |
| 19 | `692918` | Talbott Chardonnay Kali Hart 24 Ml | 6 | 1 | $85.98 |
| 20 | `0676283` | Estival Sauginon Blance (SC)24 | 6 | 1 | $78.00 |
| 21 | `696410` | Big Salt White 25 Ml | 6 | 1 | $78.00 |
| 22 | `697750` | Copain White Daybreaksc25 Ml | 6 | 1 | $66.00 |
| 23 | `683473` | Dry Creek Fume Blanchebsc24 Ml | 6 | 1 | $63.96 |
| 24 | `33497` | Dekuyper Triple Sec 1/12 1 Ltr Bottle 30pf | 1 | 1 | $57.50 |

**Southern Glazer's confirms the guide exactly**: Tuesday every week without
exception (12 of 20 invoices, $16,976 - 84% of spend), plus **Friday follow-ups in
four separate weeks** (6 invoices, $2,499). The guide flags that follow-up as
"confirm with Bethany first - not guaranteed"; the data shows it is used regularly,
about one week in three. It is a real second window, not a favour.

**Two items are a third of the account.** High Noon peach vodka seltzer is
**$6,382.48 - 152 cases across 13 of 20 invoices**, comfortably the biggest single
line. Add Red Bull regular and sugar-free at **$4,216** and the top two products
are 52% of everything Southern Glazer's sells us. The wine list underneath it is
long and thin.

**The champagne program finally appears.** Veuve Clicquot (`355642`) shows up once,
$456 for a case on 2026-09-04. An earlier audit noted the champagne program was
invisible in a 5.7-week sample; it was simply bought outside that window.


## Three more things to act on

### 1. Two Heidelberg invoices appear twice, once with a truncated number

| Pair | Invoice A | Invoice B | Content |
|---|---|---|---|
| 1 | `2919` (2026-08-12) | `900002919` (2026-08-13) | Peyrassol Rose, 1 unit, $175.95 |
| 2 | `4341` (2026-08-13) | `900004341` (2026-08-13) | Peyrassol 6 @ $14.66 + Ancient Peaks 6 @ $13.33 |

Heidelberg's invoice numbering changed mid-quarter from `92xxxxx` to `9000xxxxx`.
Each of these pairs is **the same invoice keyed twice** - once with the full new
number and once with the trailing digits only. Totals differ only in how the
service fee and credit were entered ($175.95 vs $185.95; $189.94 vs $179.94).

**This is different from the Arena case and needs a different fix.** Arena was the
vendor billing one delivery twice, and the money is recoverable from the vendor.
This is **MarginEdge holding the same document twice**, so nobody was overcharged -
but spend and depletion are double-counted, which quietly inflates the baseline for
Peyrassol and Ancient Peaks. The fix is de-duplication at ingest, not a credit
request: **normalise the invoice number (strip a leading `9000`, compare the tail)
before treating two documents as distinct.**

### 2. Bitters may be materially cheaper at Southern Glazer's than Arena

| Vendor | Code | Price | Note |
|---|---|---|---|
| Arena | `0754960020` | **$21.99** | Angostura, 2 bought |
| Arena | `0754963325` | **$21.99** | Angostura Orange, 2 bought |
| Southern Glazer's | `334995` | **$182.30** | Angostura, 1 bought |
| Southern Glazer's | `976180` | **$182.30** | Angostura Orange, 1 bought |

If the Southern Glazer's line is a **case of 12** and Arena's is a **single bottle**,
SGWS works out at about **$15.19 a bottle against Arena's $21.99 - roughly 31%
cheaper**. That is worth checking, but **it is not yet proven**: neither record
states a pack size, and I have not confirmed the SGWS unit. **Ask for the pack size
on SGWS `334995` before acting.** If it is a 12-pack, bitters should move.

### 3. Price rises worth a conversation

| Item | Vendor | First | Last | Change |
|---|---|---|---|---|
| Aperol 1L | Southern Glazer's | $142.00 | $156.95 | **+10.5%** |
| Red Bull (both SKUs) | Southern Glazer's | $42.00 | $46.00 | **+9.5%** |
| Frenzy Sauvignon Blanc | Heidelberg | $127.95 | $135.95 | +6.3% |

Red Bull is the one that matters by volume: 94 cases across the quarter, so a $4
rise is about **$376 a quarter** at current volume. Aperol is 9 units, so the
$14.95 rise is about $135.

## Two Buckeye near-pairs that are NOT duplicates

Worth recording the negatives, because they are the exact shape a duplicate-invoice
check flags and they cost time every time somebody rediscovers them.

| A | B | Why it looks like a double bill | What it actually is |
|---|---|---|---|
| `159063` 7/6, $61.45 | `159345` 7/10, $61.45 | Identical total, identical single line, four days apart, near-sequential numbers | **Two nitrogen cylinders.** Code `1011` Nitrogen Large at $61.45 each. It is the most frequently ordered line on the account (13 units in the quarter) - four days between cylinders is ordinary turnover |
| `159994` 7/24, $142.78 | `160054` 7/26, $142.78 | Identical total, both a single 5-gallon fountain line, two days apart | **Coca-Cola and Diet Coke.** Codes `100` and `101`, two distinct products that happen to share a price |

Same false-positive class as the five Superlyte flavours and Sam Adams Cherry Wheat
vs Lager from the Arena pull. **A matching total is not evidence.** The signature has
to include the item code, and the Arena double bill only held up because all 29 lines
matched on code, quantity *and* price.

Heidelberg's two pairs are the opposite case and are genuine - identical product
lines at identical unit prices, differing only in whether the fees sit in a charge
field or in a line. Detail in the Heidelberg section above.

## What is still not pulled

Line-item detail now covers **6 of 12 beverage vendors**. Remaining, by spend:

| Vendor | Invoices | Spend | Why it matters |
|---|---|---|---|
| Hillcrest | 61 | $159,381 | Largest supplier in the building, but mostly food; the bar items are known (allulose, brown sugar, cider, bevnaps, Beer Clean) |
| Amazon | 188 | $27,244 | Long-tail prep goods; no item codes at all, so line items are of limited use |
| Sixth City | 19 | $4,919 | Rotating keg program - what actually arrived is the whole question |
| Berardi's | 13 | $4,237 | Cafe coffee; volumes already estimated |
| Hartzler | 13 | $3,551 | Now known to be two items only |
| Cavalier | 9 | $3,108 | Rotating kegs plus the Bumble Berry named SKU |

**Sixth City and Cavalier are the highest-value remaining pull** despite being the
smallest by spend: they are the rotating keg program, where the guide currently says
only "ask Jenna" or "ask Dan" and has no idea what actually came through the door.

