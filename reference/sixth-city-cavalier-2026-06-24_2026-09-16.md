# Sixth City + Cavalier line items, 2026-06-24..09-16

Pulled 2026-10-01 from MarginEdge. **19 Sixth City orders ($4,919.44)** and
**9 Cavalier orders ($3,107.66)**, every line item. Both totals reconcile exactly
to the orders endpoint, so nothing is missing or double-counted in the transcription.

These are the two smallest beverage vendors by spend and the two the guide knew
least about - it said only "ask Jenna what's available" and "ask Dan". They turn out
to carry the most decision-relevant information of any vendor pulled so far.

## The headline: at $5 a pint the rotating program runs a 49.5% pour cost

**Draft is $5.00 flat across every tap** (confirmed by the operator 2026-10-01).
Every rotating keg is chosen on style off a rep's availability list, and nothing in
that conversation has ever mentioned what the keg costs to pour.

Measured against what was actually bought - **65 kegs, $7,864.35 of product, about
3,176 sixteen-ounce pours** - the program blends to a **49.5% pour cost**. Nearly
half of every draft dollar goes back out as beer, before labour, waste, or the pints
that die in the line.

**Two kegs lost money on every pour.** Not "ran thin" - cost more than the $5 they
sold for:

| Keg | Vendor | Size | Keg cost | $/pour | Pour cost |
|---|---|---|---|---|---|
| Platform Pumpkin Kerfuffle | Cavalier | 1/6 | $224.99 | **$5.74** | **115%** |
| 450 North Supersize Painkiller Slushy XXL Sour | Sixth City | 1/6 | $199.99 | **$5.10** | **102%** |
| Drekker Chonk Blueberry White Chocolate Sundae Sour | Sixth City | 1/6 | $169.99 | $4.34 | 87% |
| Lolev Osprey Ultra Hopped Ale | Sixth City | 1/6 | $169.99 | $4.34 | 87% |
| Blackstack Estate Sale DDH DNEIPA | Sixth City | 1/6 | $159.99 | $4.08 | 82% |
| *median of all 63 lines* | | 1/6 | $109.99 | *$2.55* | *51%* |
| Jolly Scholar Cold Beer Here American Lager | Sixth City | 1/6 | $64.99 | $1.66 | 33% |
| Fat Head's Bumble Berry | Cavalier | **1/2** | $169.99 | $1.45 | **29%** |
| Cult Craft Root Beer | Sixth City | 1/6 | $49.99 | $1.28 | **26%** |

**Of 63 keg lines, exactly two products clear a 30% target** - Bumble Berry and the
root beer. At a 25% target, **nothing clears at all.** Every single line is above
25%.

## The sixth-barrel format and a $5 pint do not fit together

This is the part that cannot be fixed by nagging the rep. At $5.00 for a 16oz pour,
here is the most a keg may cost:

| Format | Net oz | Pours | @ 25% | @ 30% | @ 35% | What we actually pay |
|---|---|---|---|---|---|---|
| **1/6 bbl** | 627 | 39 | $48.98 | **$58.78** | $68.58 | **$109.99 median - fails** |
| 1/4 bbl | 941 | 59 | $73.52 | $88.22 | $102.92 | $119.99 - fails |
| 50 L | 1,603 | 100 | $125.23 | $150.28 | $175.33 | $239.99 - fails |
| **1/2 bbl** | 1,880 | 118 | $146.88 | **$176.25** | $205.62 | **$169.99 - clears** |

A sixth-barrel has to cost **under $58.78**. The rotating market prices them **$90 to
$225**, and only Cult Craft Root Beer ($49.99) came in under. Loosening the target
does not rescue it: even at 35% the ceiling is $68.58, still below the cheapest real
beer on the list.

**Format is worth more than brand choice, by a wide margin.** Bumble Berry clears at
29% *because it is a half-barrel*. The identical $169.99 in a sixth-barrel would be
**87%** - three times the pour cost for the same money. Nothing about the beer
changed; only the pack.

So there are three honest levers, and this is an operator decision, not an ordering
one:

1. **Price the rotating taps separately.** A featured tap at $7-8 puts the median
   $109.99 sixth-barrel back into the high 30s and leaves the house taps at $5.
2. **Move the house taps to half-barrels.** Fewer choices, roughly half the pour
   cost. Bumble Berry is the existence proof.
3. **Keep it exactly as it is and book it as marketing.** A rotating wall of rare
   beer at a ~50% pour cost is a perfectly defensible spend *if it is a decision with
   a number attached* and the number of taps is capped. It is not defensible as an
   accident.

**One unconfirmed number changes the severity but not the conclusion: is the house
pour 16oz or 12oz?** At 12oz the same kegs blend to **37.1%** and the sixth-barrel
ceiling rises to $78.38 - still under the $109.99 median, so the structural problem
survives either way. But 49.5% and 37.1% are different conversations. One question to
a bartender settles it.

## Two more duplicate invoices, and a new root cause

**This is the third vendor in a row with a double bill, and the mechanism here is
different from the other two.** Both of these come from the same cause: TownHall
ingests invoices by two paths at once - the vendor's electronic CSV feed, and a
phone photo of the paper copy uploaded from the floor. MarginEdge merges the two
when the invoice numbers agree. When whoever keyed the photo mistyped the number,
it did not merge, and the delivery was recorded twice.

The attachments prove it. `O-5049032` and `O-5083859` each carry **both** a
`.csv` and a `Mobile Image Upload ... .jpg` on one order - merged correctly. The
two below each split into a CSV order and a photo order.

**Pair 1 - Cavalier, 7 July, letter O vs digit zero.**

| | `O-5054012` (CSV) | `0-5054012` (photo) |
|---|---|---|
| Total | $204.31 | $234.31 |
| Fat Head's Bumble Berry 1/2 | 1 @ $169.99 | 1 @ $169.99 |
| Vol Sun Goddess Prosecco | 4 @ $16.08 | 4 @ $15.33 |
| Keg deposit | +1 | +1 |
| Deposit return | -2 | -1 |
| Split case fee | in unit price | $3.00 separate |

The only difference between the invoice numbers is **`O` versus `0`**. A character
that looks identical in most fonts defeated the duplicate check completely. A third
record, `0-43820003` (-$60.00, photo), is a bare deposit-return credit for the same
day whose -2 kegs already appear inside `O-5054012`.

**Pair 2 - Sixth City, 29 July, transposed digits.**

`112661` (photo, $309.94) and `112551` (CSV, $309.96) are the same delivery:

| Keg | `112661` | `112551` |
|---|---|---|
| Drekker SMoL Blue Razz GF Sour 1/6 | $119.99 | $119.99 |
| Fair State Festbier 1/6 | $89.99 | $89.99 |
| Phase Three Lulz Pink Lemonade Seltzer 1/6 | $99.99 | $99.99 |
| Third Eye Gettin' Twisted German Pretzel Ale 1/6 | $89.99 | $89.99 |
| Deposit purchase / return | +4 / -7 | +4 / -7 |

Four identical kegs, identical prices, identical deposit quantities, same invoice
date. The numbers differ in one place - `66` against `55`.

**Detection rules this adds**, on top of the Heidelberg "strip a leading 9000" rule:

1. **Normalise homoglyphs before comparing invoice numbers**: `O`/`0`, `I`/`l`/`1`,
   `S`/`5`, `B`/`8`. The Cavalier pair differs by exactly one such substitution.
2. **Compare on the line-item set, not the invoice number**, when a vendor has two
   ingestion paths. Same vendor + same invoice date + same multiset of
   (product, quantity, price) is a duplicate whatever the number says.
3. **Know which vendors are dual-ingested.** Sixth City and Cavalier both are. That
   is a standing duplicate risk, not a one-off, and it is the reason to care that
   somebody is still photographing paper that already arrived as a CSV.

## A duplicate invoice manufactures phantom staples

This matters more than the money. Sixth City bought **45 distinct keg products** in
the quarter. Count by name and **7 of them look like repeat lines**. After removing
the duplicate invoice, **only 3 are real**:

| Product | Appears | Verdict |
|---|---|---|
| Shacksbury Blackberry Lime Cider | 6/24 and 8/5 | **Genuine repeat** |
| Jolly Scholar Cold Beer Here American Lager | 7/15 and 8/26 | **Genuine repeat** |
| Immigrant Son Gourdians Pumpkin Ale | 8/26 and 9/2 | **Genuine** - and seasonal |
| Fair State Festbier | 7/29 twice | Phantom - duplicate invoice |
| Phase Three Lulz Pink Lemonade Seltzer | 7/29 twice | Phantom - duplicate invoice |
| Third Eye Gettin' Twisted German Pretzel Ale | 7/29 twice | Phantom - duplicate invoice |
| Drekker SMoL Blue Razz GF Sour | 7/29 twice | Phantom - duplicate invoice |

So the staple test, run on raw data, would have promoted **four one-off rotating
kegs into forecast staples** - and then reordered them forever. The PRD already says
the staple test must run on item codes rather than product names, because of the
Albino Stout case. This adds a second precondition: **the staple test must run on
de-duplicated invoices.** Duplicate detection is not only an AP control, it is an
input to the forecast.

One more detail worth keeping: the Drekker phantom was **missed on the first pass**
because the two spellings are `SMoL` and `Smol`. Case-sensitive name matching found
six repeats where there were seven. Identity by name fails on capitalisation too.

**The Albino Stout collapse is now confirmed at the source.** Code `1555`
("Albino Stout White Stout", 9/2) and code `1871` ("Nitro Albino Stout", 9/16) both
carry `companyConceptProductId` **628588136**. Two different beers, two different
orders, one product id - exactly as the PRD predicted, now verified.

## 45 products, 3 repeats: the rotating program is almost entirely one-and-done

Sixth City: **45 distinct kegs, 3 repeats, 51 keg lines.** Cavalier: **11 distinct
kegs, 1 repeat.** A trailing average over this data is meaningless for all but four
products - it would read "1" for everything and keep reordering beers that were
deliberately never bought again. This is the strongest evidence yet for the PRD rule
that rotating lines are excluded from baseline learning and ordered as a
style-and-count instead.

The exception proves the rule: **Fat Head's Bumble Berry is not a rotating keg and
not a "named SKU exception" either - it is the anchor of the Cavalier account.**
5 orders, **7 half-barrels, $1,189.93 - 38% of everything Cavalier sold us.** At
0.64 kegs/week over the 11-week span it is close to the 0.7/wk the catalog already
carries, so that rate stands.

## Cavalier is not a 1/6-barrel vendor and not a keg-only vendor

The guide says "1/6 bbl only". The quarter says otherwise - **three formats**:

| Format | Kegs | Notable |
|---|---|---|
| 1/6 bbl | 9 | the rotation |
| 1/2 bbl | 5 | all Bumble Berry |
| 1/4 bbl | 1 | Cider Caramel Apple, $119.99 - the first 1/4 bbl in the data |

And **$429.84 of the account is not beer at all**: Fab Amarena Cherries Syrup
(bar prep, 6 cases across two orders), Giffard Rhubarb Liqueur (6 bottles) and
Vol Sun Goddess Prosecco Rosé (12 bottles). Cavalier is a mixed account - kegs,
bar prep and wine. Ordering it as "rotating kegs, ask Dan" leaves the cherries and
the rhubarb to memory.

The Prosecco appears at **$15.33 and $16.08** for the same bottle - the split-case
fee folded into the unit price on one path and broken out as a $3.00 charge on the
other. Same pack-size artifact as the Heidelberg wines; not a price increase.

## Both deposit ledgers are clean - unlike Superior

Once the duplicate records are removed:

| Vendor | Deposits charged | Returned | Net float |
|---|---|---|---|
| Sixth City | 47 kegs ($1,410) | 44 ($1,320) | **$90** |
| Cavalier | 17 kegs ($510) | 14 ($420) | **$90** |

Three kegs outstanding each, which is what a bar with live taps should look like.
Compare **Superior at $990 and drifting**. Sixth City and Cavalier are the control
group that shows the Superior number is a real problem rather than normal slippage.

## But Sixth City's credit records are double-counted - and this one favours us

Six Sixth City deposit returns exist **twice**: once as a line inside the invoice,
and again as a standalone credit order numbered with a `C` suffix. Every `C` record
is an empty stub - **no line items, no attachment, `isCredit: true`** - whose total
matches its parent's return line exactly.

| Stub | Amount | Parent's return line |
|---|---|---|
| `110945C` | -$210.00 | -7 x $30 inside `110945` |
| `111842C` | -$90.00 | -3 x $30 inside `111842` |
| `112661C` | -$210.02 | -7 x $30 inside `112661` |
| `113069C` | -$30.00 | -1 x $30 inside `113069` |
| `113489C` | -$150.00 | -5 x $30 inside `113489` |
| `113833C` | -$150.00 | -5 x $30 inside `113833` |
| *(no invoice number)* | -$30.00 | orphan stub, 6/24 |
| **Total** | **-$870.02** | |

**Direction matters here.** Arena's $5,781.06 and Heidelberg's $365.89 were us
paying twice. This is the reverse: **if AP processed both the invoice and the credit
stub, TownHall took $870.02 of credit it was only owed once, and underpaid Sixth
City.** Worth checking against what was actually remitted before anybody asks them
for anything. A duplicate-detection rule that only looks for overpayment will never
surface this.

The `112661C` stub is **-$210.02**, two cents off the -$210.00 it mirrors. That
rounding is a tell that it arrived by a different path from the invoice itself.

## The fall brief has already changed - the written one is just stale

Open question 22 asks what the fall/winter brief should be. The buying already
answered it, and the pivot lands on **16 August**:

| Style | Through 8/15 | From 8/16 |
|---|---|---|
| Sour / fruited | **9** | 3 |
| Cider | **4** | 0 |
| Seltzer / NA | 2 | 0 |
| Lager / pils | 6 | 3 |
| IPA / pale | 4 | 3 |
| Pumpkin / Märzen / Oktoberfest | 2 | **9** |
| Dark / stout / porter | 0 | **4** |
| Barrel / specialty | 2 | 4 |
| **Total kegs** | **32** | **33** |

Same volume, different beer. Sours fell from 9 to 3, cider went to zero, pumpkin
and Märzen went from 2 to 9, and dark beer appeared from nothing. The standing
instruction - "summer: sours, smoothies, pale ales" - describes the left column of
a table the bar stopped living in six weeks ago.

**What the brief should say now**, straight off the invoices: pumpkin and Märzen
first, then porter and stout, barrel-aged as the specialty slot, two or three sours
to keep the range, no cider. And a price ceiling, which it has never had.

## Every product, both vendors

Quantity is units bought in the window; "Ord" is how many separate orders it
appeared on. $/pint uses net-of-foam yields and is blank for non-keg items.

| Product | Vendor | Code | Size | Unit $ | Qty | Ord | $/pint |
|---|---|---|---|---|---|---|---|
| 450 North Supersize Painkiller Slushy XXL Sour | Sixth City | - | 1/6 | $199.99 | 1 | 1 | $5.10 |
| Aval Blanc French Cider | Sixth City | - | 1/6 | $114.99 | 1 | 1 | $2.93 |
| Blackstack Estate Sale DDH DNEIPA | Sixth City | - | 1/6 | $159.99 | 1 | 1 | $4.08 |
| Butcher And The Brewer Albino Stout White Stout | Sixth City | 1555 | 1/6 | $79.99 | 1 | 1 | $2.04 |
| Butcher And The Brewer Nitro Albino Stout | Sixth City | 1871 | 1/6 | $79.99 | 1 | 1 | $2.04 |
| Butcher and The Brewer Scenes from A Restaurant Italian Pilsner | Sixth City | - | 1/6 | $69.99 | 1 | 1 | $1.79 |
| Cider Caramel Apple | Cavalier | 26120 | 1/4 | $119.99 | 1 | 1 | $2.04 |
| Cult Craft Root Beer | Sixth City | 8605 | 1/6 | $49.99 | 1 | 1 | $1.28 |
| Drekker Brunch Bubbz Mimosa Sour | Sixth City | - | 1/6 | $129.99 | 1 | 1 | $3.32 |
| Drekker Chonk Blueberry White Chocolate Sundae Sour | Sixth City | - | 1/6 | $169.99 | 1 | 1 | $4.34 |
| Drekker Smol Blue Razz GF Sour | Sixth City | 6631 | 1/6 | $119.99 | 1 | 1 | $3.06 |
| Fab Amarena Cherries Syrup 6/8oz | Cavalier | 16234 | case | $19.99 | 6 | 2 | - |
| Fair State Festbier | Sixth City | 2610 | 1/6 | $89.99 | 1 | 1 | $2.30 |
| Fair State Pahlay Tropical Pale Ale | Sixth City | 7793 | 1/6 | $89.99 | 1 | 1 | $2.30 |
| Fat Head's Bumble Berry | Cavalier | 4824 | 1/2 | $169.99 | 7 | 5 | $1.45 |
| Fat Head's Spooky Tooth | Cavalier | 5356 | 1/6 | $129.99 | 1 | 1 | $3.32 |
| Foam Brewers Allen Observer Fruited Sour | Sixth City | - | 1/6 | $129.99 | 1 | 1 | $3.32 |
| Foam Brewers Disco Lemonade Tart Wheat Ale | Sixth City | - | 1/6 | $129.99 | 1 | 1 | $3.32 |
| Foam Brewers Tranquil Pils | Sixth City | - | 1/6 | $94.99 | 1 | 1 | $2.42 |
| Fonta Flora Darwin's Forehead Porter | Sixth City | - | 1/6 | $139.99 | 1 | 1 | $3.57 |
| Giffard Liqueur Rhubarb 750ml | Cavalier | 17952 | btl | $19.99 | 6 | 1 | - |
| Hidden Springs Humble Pie Sour Ale | Sixth City | - | 1/6 | $139.99 | 1 | 1 | $3.57 |
| Hop Smashing Honey Blonde | Cavalier | 24458 | 1/6 | $119.99 | 1 | 1 | $3.06 |
| Hop Turbo Shandy Blackberry | Cavalier | 29091 | 1/6 | $99.99 | 1 | 1 | $2.55 |
| Hopewell Going Places American IPA | Sixth City | 6653 | 1/6 | $99.99 | 1 | 1 | $2.55 |
| Hopewell Oktoberfest Marzen | Sixth City | - | 1/6 | $89.99 | 1 | 1 | $2.30 |
| Immigrant Son Acapulco Gold 2026 Golden Ale | Sixth City | - | 1/6 | $109.99 | 1 | 1 | $2.81 |
| Immigrant Son Blue Pearl Blueberry Kolsch | Sixth City | 6111 | 1/6 | $109.99 | 1 | 1 | $2.81 |
| Immigrant Son Gourdians Pumpkin Ale | Sixth City | 5006 | 1/6 | $99.99 | 2 | 2 | $2.55 |
| Jolly Scholar Cold Beer Here American Lager | Sixth City | 882 | 1/6 | $64.99 | 2 | 2 | $1.66 |
| Lexington KY BB Cocoa Porter | Cavalier | 26342 | 1/6 | $109.99 | 1 | 1 | $2.81 |
| Lexington KY Vanilla Barrel Ale | Cavalier | 13985 | 1/6 | $94.99 | 1 | 1 | $2.42 |
| Lolev Osprey Ultra Hopped Ale | Sixth City | - | 1/6 | $169.99 | 1 | 1 | $4.34 |
| Moody Tongue Aperitif Pilsner German Pilsner | Sixth City | - | 1/6 | $99.99 | 1 | 1 | $2.55 |
| Perennial Baggy Jeans TIPA w/ Honey | Sixth City | 7306 | 1/6 | $139.99 | 1 | 1 | $3.57 |
| Perennial Coastal Arch West Coast Pils | Sixth City | - | 1/6 | $109.99 | 1 | 1 | $2.81 |
| Perennial Poolside Breeze Fruited Berliner Weisse | Sixth City | 3762 | 1/6 | $109.99 | 1 | 1 | $2.81 |
| Perennial Vacation Dad Summer Ale | Sixth City | 995 | 1/6 | $99.99 | 1 | 1 | $2.55 |
| Phase Three Lake Trip American Pale Ale | Sixth City | - | 1/6 | $119.99 | 1 | 1 | $3.06 |
| Phase Three Lulz Pink Lemonade Seltzer | Sixth City | 4376 | 1/6 | $99.99 | 1 | 1 | $2.55 |
| Phase Three So Ripe Peach Strawberry Sour Ale | Sixth City | - | 1/6 | $139.99 | 1 | 1 | $3.57 |
| Platform Pumpkin Kerfuffle | Cavalier | 23422 | 1/6 | $224.99 | 1 | 1 | $5.74 |
| Shacksbury Blackberry Lime Cider | Sixth City | 5993 | 1/6 | $99.99 | 2 | 2 | $2.55 |
| Shacksbury Jungle Bird Cider | Sixth City | 9409 | 1/6 | $99.99 | 1 | 1 | $2.55 |
| Sinister Black Window | Cavalier | 14887 | 1/6 | $124.99 | 1 | 1 | $3.19 |
| The Veil Bend IPA | Sixth City | - | 1/6 | $109.99 | 1 | 1 | $2.81 |
| Third Eye Drittes Auge Marzen Oktoberfest | Sixth City | 6522 | 1/6 | $79.99 | 1 | 1 | $2.04 |
| Third Eye Enlightenment Blood Orange Wheat | Sixth City | 7479 | 1/6 | $99.99 | 1 | 1 | $2.55 |
| Third Eye Funky Diablo V3 Mango Habanero Margarita Sour | Sixth City | - | 1/6 | $129.99 | 1 | 1 | $3.32 |
| Third Eye Gettin Twisted German Pretzel Ale | Sixth City | 6610 | 1/6 | $89.99 | 1 | 1 | $2.30 |
| Third Eye Pumpkin P-Eye Pumpkin Ale | Sixth City | - | 1/6 | $109.99 | 1 | 1 | $2.81 |
| Third Eye Pumpkin P-Eye Pumpkin Spice Ale | Sixth City | 6525 | 1/6 | $109.99 | 1 | 1 | $2.81 |
| Third Eye Small Batch Series Berry Shandy | Sixth City | 9411 | 1/6 | $89.99 | 1 | 1 | $2.30 |
| Tripping Animals Dark No Mames Mexican Dark Lager | Sixth City | - | 1/6 | $99.99 | 1 | 1 | $2.55 |
| Tripping Animals Pumpkin Delic Pumpkin Beer | Sixth City | 5024 | 1/6 | $109.99 | 1 | 1 | $2.81 |
| Urban Artifact Jack | Cavalier | 27158 | 1/6 | $119.99 | 1 | 1 | $3.06 |
| Urban Artifact Whirligig | Cavalier | 13460 | 1/6 | $139.99 | 1 | 1 | $3.57 |
| Vol Sun Goddess Prosecco Rose DOC | Cavalier | 26705 | btl | $16.08 | 8 | 2 | - |
| Voodoo Purple Lacto-Kooler Sour Ale | Sixth City | 9287 | 50L | $239.99 | 1 | 1 | $2.40 |

## What is still not pulled

Line-item detail now covers **8 of 13 beverage vendors**. Remaining:

| Vendor | Invoices | Spend | Why it matters |
|---|---|---|---|
| Hillcrest | 63 | ~$159K | Largest supplier, mostly food; bar items already known |
| Amazon | 206 | ~$27K | Long-tail prep goods, no item codes, limited value |
| Berardi's | 13 | ~$4.2K | Cafe coffee; volumes already estimated |
| Hartzler | 13 | ~$3.6K | Confirmed two items only - nothing left to learn |

**None of the remaining four is worth a pull for ordering purposes.** The beverage
program is now fully mapped at line-item level, and no further vendor pull will
change a decision.

The three things actually worth doing, in order:

1. **Decide what to do about a 49.5% draft pour cost.** Price the rotating taps,
   move house taps to half-barrels, or cap it and call it marketing. Confirm the
   16oz-vs-12oz pour first, since it moves the number 12 points.
2. **Chase the credits.** Four duplicate billings across three vendors - Arena
   $5,781.06, Heidelberg $365.89, Cavalier $234.31, Sixth City ~$310 - plus Sixth
   City's $870.02 of double-counted credits running the *other* way, where TownHall
   may have underpaid. About $7,500 of AP discrepancy, no owner.
3. **Get Buckeye's cutoff from the rep**, so the catalog has no blanks left.
