# Flag Research — Margin Edge

Answers to the order guide's open flags, pulled read-only from **Margin Edge** on **2026-09-29**.

Units queried: **TownHall – Columbus = 166233400**, **TownHall – Cleveland = 166232982**.
Tools used: `Get_vendor_items_by_product`, `Get_product_price_history`, `Get_recipe_ingredients`.

Everything below is either quoted from a tool response or arithmetic on quoted numbers. Where a
query returned nothing, that is stated plainly. Nothing here is a guess at a vendor or pack size.

---

## Summary

| # | Question | Status | One-line answer |
|---|---|---|---|
| 1 | Cocoa powder SKU | **RESOLVED** | `Spice, Cocoa Powder` — Columbus buys **Whole Foods "Nvtn Og Cacao Powder"** ($14.24 EA, last **2024-05-25**, 2 yrs stale); Cleveland actively buys **Anthony's Organic Cocoa Powder 5 lb, Amazon, $49.99** (2025-12-01). A real SKU exists; nothing needs sourcing. |
| 2 | Chia seeds vendor | **RESOLVED** | **Costco**, item code **1309922 "Org Chia"**, **$8.79 EA**, bought ~2–4×/month at both units. **Not** a broadline distributor. Pack size is not recorded in ME. |
| 3 | Chocolate collagen | **RESOLVED** | Not different vendors. **Columbus has zero vendor items and exactly one price point — 2022-02-18 — 4.5 years old.** Cleveland is the only unit actually buying it. The recon doc's "both last priced 2025-09-29" is wrong. |
| 4 | Matcha | **RESOLVED** | A **different, cheaper matcha**: Amazon *"Organic Matcha Green Tea Powder 2lb First Harvest **Culinary Grade**"*, $42.99 / 2 lb. Not Santé. |
| 5 | Cashew butter | **RESOLVED** | `Butter, Cashew` — **Amazon, Kevala Cashew Butter, 7 LB tub, $82.11** (last 2026-06-21) → $11.73/lb. Reproduces the $8.53 / 330 g exactly. |
| 6 | Vanilla collagen | **RESOLVED** | **Amazon, Vital Proteins Collagen Peptides Vanilla, 10.6 oz, $27.95** (2026-08-18). A *different product* from Orgain, and **ME's pack conversion is wrong by 1.82×** — the true cost is $0.093/g, not $0.0511/g. |
| 7 | Zero-cost products | **RESOLVED — premise does not hold** | **None of the three is $0.00.** Coconut Cream, Chai and Sea Moss all have live prices at both units. Separate error found: **sea moss is costed at 2× because ME assumes an 8 oz pack for a 1 lb bag.** |
| 8 | Water | **RESOLVED — root cause found** | Columbus's only "Water" vendor item is a **$49.10 case of San Pellegrino Sparkling from Chefs Warehouse**, mapped as **1 case = 1 gallon**. 110/128 × $49.10 = **$42.20** exactly. Cleveland has no vendor item and reads $0.00. |
| 9 | Peanut butter powder | **PARTIALLY RESOLVED** | **No vendor exists to find.** Zero vendor items at *both* units. Columbus price history is empty back to 2020; Cleveland has one point (2024-12-26, $1.36/oz). The $78.71 has no traceable source. |
| 10 | Perfect Keto product | **RESOLVED** | Confirmed **Nootropic Brain Support**, Amazon.com, and the *vendor line-item names* say Nootropic too — so this is a real purchasing fact, not a mislabeled record. |

---

## Flag 1 — Cocoa powder SKU

**Product 171723988 · `Spice, Cocoa Powder` · report-by unit `1.00 POUND`**

### Columbus (166233400) — 3 vendor items

| Vendor | Vendor item | Packaging | Price | Conv. ratio | Last ordered |
|---|---|---|---|---|---|
| **Whole Foods Market** | `Nvtn Og Cacao Powder` | EA | **$14.24** | 0.5 | **2024-05-25** |
| Whole Foods Market | `NN Og Mayan Cocoa Suprfd` | EA | $11.79 | 0.67 | 2023-01-06 |
| Amazon | `Navitas Organics Organic Cacao Powder, Non-Gmo, Fair Trade, Gluten-free` | EA/24OZ | $19.82 | 0.67 | 2023-03-18 |

Columbus price history — 10 points, **2023-01-06 → 2024-05-25**, all in $/POUND:
$10.00 · $13.14 · $13.21 · $11.29 · $13.21 · $5.90 · $10.00 · $7.95 · $9.00 · **$7.12 (latest, 2024-05-25)**

$7.12/lb ÷ 453.6 g = **$0.0157/g = $1.57 / 100 g** — exactly the Keto recipe line. The costing
traces to the Whole Foods item ($14.24 × 0.5 conversion ratio = $7.12/lb).

### Cleveland (166232982) — 12 vendor items, actively bought

Current: **Amazon, `Anthony's Organic Cocoa Powder, 5 lb, Unsweetened, Gluten Free, Non Gmo`,
EA/5LB, $49.99, last ordered 2025-12-01** → $10.00/lb = **$2.20 / 100 g**.
Others on the guide include Anthony's Organic Culinary Grade 1 lb ($18.99, 2025-11-21), several
Healthworks 5 lb listings ($39.99–$49.99), and Catanese Classics `Coco Power Dutch process Gallon`
EA/4.8LB $29.68 (2022-03-07).

Cleveland has ~100 price points from 2022-02-15 through 2025-12-01, mostly $8.00–$10.00/lb.

### Answer

**The order guide does not need a new SKU.** Two defensible options:

- **Anthony's Organic Cocoa Powder, 5 lb, Amazon, $49.99** — Cleveland's current buy, orderable on
  the same Amazon account as the rest of the prep. Keto uses 100 g/batch → a 5 lb bag is **~22 batches**.
- Whole Foods `Nvtn Og Cacao Powder` — what Columbus's cost is built on, but not bought since
  May 2024.

⚠️ **Caveat:** the Whole Foods vendor item records no pack weight (packaging is just `EA`). ME
infers 2 lb from the 0.5 conversion ratio. If the real Whole Foods pack is 1 lb, Columbus's cocoa
cost is understated 2×. **I did not see a pack size in the data and am not asserting one.**

⚠️ Columbus's cocoa price is **2 years 4 months stale** and 29% below Cleveland's current $10.00/lb.

---

## Flag 2 — Chia seeds vendor

**Product 176715756 · `Chia Seed` · report-by unit `1.00 EACH`**

### Columbus — 2 vendor items, both Costco

| Vendor | Item code | Vendor item | Price | Last ordered |
|---|---|---|---|---|
| **Costco** (vendorId 167201) | **1309922** | `Org Chia` | **$8.79** | **2026-09-08** |
| Costco | 1253040 | `Chia Seed` | $8.99 | 2023-12-27 |

Columbus price history: **49 price points, 2022-12-05 → 2026-09-08.** Bought ~2–4× per month,
continuously. $8.99 (2022–23) → $8.49 (2024 – Oct 2025) → $8.69 → **$8.79 (current)**.
ME's own per-ounce figure held at **$0.18/oz** throughout.

### Cleveland — 8 vendor items, Costco plus Amazon

- **Costco Wholesale**, item code **1309922 `ORG Chia`, $8.79, last 2026-08-18** (same SKU as Columbus)
- Amazon `BBF Organic Chia Seeds 32 Oz`, EA/32OZ, **$13.97, last 2026-09-16** — this is **the exact
  SKU the Amazon research priced** ($13.97 / 2 lb jar)
- Amazon `Greenfit Premium Bulk Chia Seeds`, packaging Bag/25LB, **$82.16**, last 2025-09-25
- Amazon `Healthworks ... 96 Oz / 6 Lbs`, $25.64, last 2025-09-15
- Amazon `BetterBody Foods Organic Chia 2 lbs`, $9.31 (2025-09-02) and $13.97 (2026-07-29)
- Amazon `365 By Whole Foods Organic Black Chia Seeds`, EA/15OZ, $13.01, last 2023-09-29

### Answer

**No — not a broadline distributor.** It is **Costco**, a club store, item code **1309922**, at
**$8.79 each**, bought steadily at both locations. That is why ME is 2.4× cheaper than the Amazon
jar: TownHall already buys chia at Costco and the Amazon jar is the same brand at retail
(Cleveland has both SKUs on its guide, at $8.79 and $13.97).

⚠️ **Pack size is not recorded in Margin Edge.** The unit is `EACH` and the packaging field is
just `EA`. ME's derived $0.18/oz implies ≈48.8 oz (~3 lb), which is consistent with Costco's
3 lb organic chia bag — **but that pack size is inferred from ME's conversion factor, not read
from the data.** Confirm the bag weight in the walk-in before using it to compute order quantities.

Recipe cross-check: Strawberry's 1,200 g line costs $7.75 → $0.00646/g, consistent with
$8.79 / ~1,383 g.

⚠️ Cleveland's **Greenfit 25 lb bag at $82.16 = $3.29/lb ($0.0072/g)** is by far the cheapest chia
in the system — about half the Costco per-gram — but the listing title says "5lbs Bag" while the
packaging field says `Bag/25LB`. **Contradictory; do not act on it without checking.**

---

## Flag 3 — Chocolate collagen (the biggest finding)

**Product 171721217 · `Powder, Collagen Peptides Protein, Chocolate` · report-by unit `1.00 EACH`**

### Columbus — the price is orphaned

- `Get_vendor_items_by_product` (166233400, 171721217) → **`"vendorItems": []`. Empty. No vendor item
  at all.**
- `Get_product_price_history` (166233400, from 2022-01-01) → **exactly one date:**

| Date | EACH | Ounce | Tablespoon |
|---|---|---|---|
| **2022-02-18** | **$56.76** | $2.94 | $0.95 |

That is the entire Columbus record. **One invoice, 2022-02-18, four and a half years ago, with no
vendor item behind it.**

### Cleveland — actively purchased, 6 vendor items

| Vendor | Vendor item | Packaging | Price | Ratio | Last ordered |
|---|---|---|---|---|---|
| **Amazon.com** | `Orgain Keto Collagen Protein Powder with MCT Oil, Chocolate` | EA | **$26.99** | 1 | **2025-09-25** |
| Amazon.com | `Bulletproof Chocolate Collagen Protein Powder ... 42.3OZ Value Size` | EA/42.3OZ | $78.39 | 1 | 2025-09-22 |
| Amazon.com | `Bulletproof ... 42.3 Oz, Value Size` | EA/42.3OZ | $59.99 | 1 | 2025-08-04 |
| Amazon.com | `Orgain Keto Collagen ... Chocalate` (B07Q1YTD1P) | EA | $23.29 | 2 | 2025-08-30 |
| Amazon.com | `Bulletproof ... 14.3 Oz` | EA/42.3OZ | $69.29 | 1 | 2025-03-01 |
| **Bulletproof** (direct) | `Chocolate Collagen Protein` (Nut05-00014) | EA/17.6OZ | $31.50 | 1 | 2023-05-15 |

Cleveland price history: **~90 price points, 2022-02-16 → 2025-09-25.** Bought weekly-to-fortnightly
for years. Latest: **$26.99 EACH / $1.40 oz, 2025-09-25.**

### Answer

**They are not buying from different vendors. Columbus is not buying it at all — in Margin Edge.**

- Columbus's **$56.76** is a single orphaned 2022 price point with no vendor item. It has never
  been corrected and cannot be, because nothing feeds it.
- Cleveland's **$26.99** is a live Amazon price for **Orgain Keto Collagen Protein Powder with MCT
  Oil, Chocolate** — the same product family the Amazon research priced at $28.25.
- **The recon doc's "both last priced 2025-09-29" is wrong.** Columbus: 2022-02-18. Cleveland: 2025-09-25.

### ⚠️ The "19.3 oz pack" is not a pack

$56.76 ÷ $2.94 = 19.31 oz. $26.99 ÷ $1.40 = 19.28 oz. Both units show the same implied pack because
**19.3 oz is a product-level `EACH → Ounce` conversion factor, not a real package.** Cleveland's
actual purchases span **17.6 oz, ~14.1 oz (Orgain) and 42.3 oz** packs, all collapsed onto one
`EACH`. Every per-ounce and per-gram cost derived from this product is therefore unreliable at
**both** units.

### Money

Longevity Powder Mix carries an identical 3,000 g chocolate-collagen line at both units:
Columbus **$311.22**, Cleveland **$147.98**. Repricing Columbus onto Cleveland's $26.99 basis is
worth **~$163/batch**, and it is a **data fix, not a negotiation** — Columbus has no supplier
relationship here to renegotiate.

---

## Flag 4 — Matcha

**Product 170593424 · `Powder, Matcha Green Tea` · report-by unit `1.00 EACH`**

### Columbus — 1 vendor item

> Vendor: **Amazon**
> Item: **`Organic Matcha Green Tea Powder 2lb First Harvest Culinary Grade Single Ingredient Green tea powder Gluten Dairy Soy & Tree Nut Free`**
> Packaging: **EA/2LB**, unit POUND, quantity 2 · **Price $42.99** · Last ordered **2026-09-08**

Columbus price history: one point, **2026-09-08, $21.50 per unit / $1.34 per ounce**.
$1.34/oz ÷ 28.35 = **$0.0474/g**, which reproduces the Being Brigid line exactly
(**54 g → $2.56**, verified in `Get_recipe_ingredients` for recipe 327175351).

### Cleveland

Price history: one point, **2022-02-07, $14.91 EACH / $0.93 per ounce**. Four and a half years
stale. *(I did not pull Cleveland's matcha vendor items.)*

### Answer

**It is a different, much cheaper matcha — explicitly labeled Culinary Grade.** A 2 lb Amazon bag
at $42.99 ($0.0474/g) against Santé CoffeeHouse **Ceremonial** at $0.297/g — **6.3×**.

Per Being Brigid batch (54 g): **$2.56 culinary vs $16.04 Santé — a $13.48/batch gap.**

This is a genuine product decision, not a data error. Ceremonial-grade matcha in a blended
smoothie powder is a quality choice someone made; ME says the kitchen is currently buying culinary
grade on Amazon. **See "Needs Taylor" below.**

---

## Flag 5 — Cashew butter

**Product 965856822 · `Butter, Cashew` · report-by unit `1.00 POUND`**

### Columbus — 3 vendor items

| Vendor | Vendor item | Packaging | Price | Ratio | Last ordered | On order guide |
|---|---|---|---|---|---|---|
| **Amazon** | **`Kevala Cashew Butter - Spreadable Cashew Cream ... No Palm Oil And No Preservatives`** | **EA/7LB** (qty 7, unit POUND) | **$82.11** | 0.14 | **2026-06-21** | yes |
| Instacart | `Fresh Ground Cashew Butter per unit` | LB | $11.89 | 1 | 2025-08-25 | yes |
| Target | `Good & Gather` | EA | $4.99 | 2.5 | 2026-04-01 | **no** |

Columbus price history (all $/POUND):
**$11.73 (2026-06-21)** · $11.73 (2026-06-12) · $11.73 (2026-04-30) · $11.73 (2026-04-27) ·
$12.48 (2026-04-01) · $11.89 (2025-08-25)

### Answer

- **Name:** `Butter, Cashew`
- **Vendor:** **Amazon** (current). Instacart is a secondary source; Target is off the order guide.
- **Pack size:** **7 lb tub** (Kevala), **$82.11**
- **Current cost:** **$11.73/lb = $0.02586/g**

Cross-check: 330 g = 0.7275 lb × $11.73 = **$8.53** — matches the Being Brigid Liquid Mix line
exactly. ✅ This one is clean: real vendor, real pack, current price, correct math.

Order math: 330 g/batch, 7 lb tub = 3,175 g → **~9.6 batches per tub.**

---

## Flag 6 — Vanilla collagen

**Product 176423390 · `Powder, Collagen Peptides Protein, Vanilla` · report-by unit `1.00 EACH`**

### Columbus — 1 vendor item

> Vendor: **Amazon**
> Item: **`Vital Proteins Collagen Peptides Powder, Vanilla, 10.6oz`**
> Packaging: **EA/10.6OZ** · **Price $27.95** · Last ordered **2026-08-18**

Columbus price history: one point, **2026-08-18 — EACH $27.95, Ounce $1.45, Tablespoon $0.47**.

### ⚠️ ME's pack conversion is wrong

$27.95 ÷ $1.45/oz = **19.28 oz assumed**, but **the vendor item says 10.6 oz**. ME is spreading the
cost over 1.82× more product than it buys.

| | ME | True (10.6 oz = 300.5 g) |
|---|---|---|
| Per gram | $0.0511 | **$0.0930** |
| Being Brigid, 900 g | $45.98 | **$83.72** (+$37.74) |
| Strawberry Skin, 400 g | $20.43 | **$37.21** (+$16.78) |
| **Per full cycle (1,300 g)** | **$66.41** | **$120.93 (+$54.52)** |

*(Both recipe lines verified directly: 900 g / $45.98 in recipe 327175351, 400 g / $20.43 in
recipe 973657060.)*

Note the same **19.3 oz** factor appears on chocolate collagen — the two collagen products share a
bad conversion.

### Comparison to the Amazon Orgain SKU

| | ME (Vital Proteins) | Amazon research (Orgain) |
|---|---|---|
| Product | Vital Proteins Collagen Peptides, Vanilla | Orgain Keto Collagen Protein w/ MCT Oil, Vanilla |
| Pack | 10.6 oz (300.5 g) | 400 g (14.1 oz) |
| Price | $27.95 | $28.25 |
| **$/g** | **$0.0930** | **$0.0706** |

**These are different products** — Vital Proteins is plain collagen peptides; Orgain Keto Collagen
adds MCT oil. On true per-gram cost, **Orgain is 24% cheaper than what Columbus is actually
buying**, the reverse of what ME's numbers suggest. Over 1,300 g/cycle that is **~$29**. It is a
product substitution, so it needs a taste/spec call.

### Cleveland

Two price points: **2025-01-02 $28.48** and **2025-01-06 $21.74 ($1.13/oz)**. 20 months stale.
*(I did not pull Cleveland's vendor items for this product.)*

---

## Flag 7 — "Zero-cost" products

**The premise does not hold. None of the three prices at $0.00 at either unit.** All three have
live price history. Details:

### Coconut Cream — product 220567603 (`1.00 EACH`)

**Columbus, 5 vendor items:**

| Vendor | Item | Packaging | Price | Last ordered |
|---|---|---|---|---|
| Amazon | `365 by Whole Foods Market, Organic Coconut Cream, 13.5 Fl Oz` | Pack/13.5OZ | **$2.99** | **2026-09-07** |
| Amazon | `Roland Foods Organic Unsweetened Coconut Cream, 13.52 Ounce Can` | EA | $6.19 | 2026-09-04 |
| Whole Foods Market | `365 ... Organic Coconut Cream, 13.5 Fl Oz` | EA/13.5OZ | $2.99 | 2026-08-23 |
| Amazon | `Roland Food Organic Unsweetened Coconut Cream ... 13.52 Ounce Can Pack` | EA/13.52 Can | $6.19 | 2026-06-16 |
| Market District | `Coconut Cream` | EA | $5.49 | 2026-02-06 |

Columbus price history: **18 points, 2026-02-06 → 2026-09-07.** Latest **$2.99**. Range $2.59–$6.19.
Cleveland price history: **36 points, 2025-08-21 → 2026-09-14.** Latest **$3.79**. Range $2.18–$6.19.

**Verdict: fully costed at both units.** The $2.99 / $3.79 in Being Brigid Liquid Mix is correct
and current. ⚠️ Note the **$2.99 vs $6.19 spread** — the same 13.5 oz can is on the Columbus guide
from two vendors at 2× the price.

### Tea, Loose Leaf Chai — product 185819908 (`1.00 CASE`)

**Columbus, 1 vendor item:** **Inca Tea**, `Loose Leaf:Pacha Chai`, packaging **LB**, quantity 1,
**$19.00**, conversion ratio 1, last ordered **2025-10-22**.

| Unit | Columbus | Cleveland |
|---|---|---|
| Latest | **$19.00 / CASE (2025-10-22)** | **$16.00 / CASE (2023-05-19)** |
| Prior | $16.00 (2023-03-27) | — |

**Verdict: costed at both units, not $0.00.** Two issues instead:
- ⚠️ **Cleveland is 3 years 4 months stale** (one price point ever, 2023).
- ⚠️ **Unit mismatch:** the product reports by `CASE` but its only vendor item is priced per
  `POUND` with conversion ratio 1 — ME is treating **1 lb = 1 case**. Any recipe line in cases or
  pounds will be off unless the case genuinely is 1 lb.

### Powder, Sea Moss Irish — product 965859033 (`1.00 EACH`)

**Columbus, 3 vendor items — all Amazon, all Nutricost, all 1 LB:**

| Item | Packaging | Price | Last ordered |
|---|---|---|---|
| `Nutricost Organic Irish Moss Powder (1 LB) Gluten Free, GMO-Free` | LB | **$27.55** | **2026-07-27** |
| `Nutricost Organic Irish Moss Powder (1 LB) - Gluten Free, Non-GMO, Vegetarian Friendly` | LB | $24.70 | 2026-05-19 |
| `: Nutricost Organic Irish Moss Powder (1 LB) ...` | EA | $24.70 | 2026-04-28 |

| Unit | Latest | Per oz | Points |
|---|---|---|---|
| Columbus | **$27.55 (2026-07-27)** | $3.44 | 3 (2026-04-28 → 2026-07-27) |
| Cleveland | **$21.97 (2026-08-10)** | $2.75 | 8 (2025-08-21 → 2026-08-10) |

**Verdict: costed at both units, not $0.00.** But a **new error** surfaced:

⚠️ **ME assumes an 8 oz pack for a 1 lb bag.** $27.55 ÷ $3.44/oz = **8.01 oz**, while every vendor
item says **1 LB**. **Sea moss is overstated 2× at Columbus.** Strawberry Skin Powder's 14 g line
reads **$1.70** (verified in recipe 973657060); at the true $27.55/453.6 g = $0.0607/g it should be
**~$0.85**. Small in dollars (~$0.85/batch), but it is the same class of pack-size error as the
collagens, on a third product.

### Where the $0.00 came from

I checked the Columbus ingredient lines of **Keto Powerhouse Powder (329621048)**, **Being Brigid
Powder Mix (327175351)** and **Strawberry Skin Powder (973657060)** directly — **no $0.00 lines in
any of them**, and sea moss reads $1.70. The recon doc shows Coconut Cream at $2.99 (Columbus) and
$3.79 (Cleveland) in Being Brigid Liquid Mix. **I was not able to find a recipe where any of these
three prices at $0.00, and the product-level data says all three are priced at both units.** If a
$0.00 was seen on screen, it is most likely a *unit-conversion* failure on a specific recipe line
(the product has no conversion to the unit the line uses), not a missing price — the same class of
fault as the chai `CASE`/`POUND` mismatch. That would need the specific recipe to pin down.

---

## Flag 8 — Water (root cause found)

**Product 177716372 · `Water` · report-by unit is literally named `Water` · unit `GALLON`**

### Columbus — 1 vendor item, and it explains everything

> Vendor: **Chefs Warehouse** (vendorId 436572)
> Item code: **GW115** · Item name: **`San Pellegrino Water Sparkling`**
> Packaging: **`Case/24/500ML Btl`**, unit BOTTLE, quantity 24
> **Price: $49.10** · **conversionRatio: 1** · Last ordered **2025-09-19**

Columbus price history — **one point:**

| Date | Unit | Price |
|---|---|---|
| 2025-09-19 | `Water` (= 1 GALLON) | **$49.10** |
| 2025-09-19 | Gram | $0.01 |

### The arithmetic reproduces both reported figures exactly

| Recipe line | Calculation | Result | Reported |
|---|---|---|---|
| 110 fl oz | 110 ÷ 128 × $49.10 | **$42.199** | **$42.20** ✅ |
| 32 fl oz | 32 ÷ 128 × $49.10 | **$12.275** | **$12.28** ✅ |

**Unit price: $49.10 per gallon** — which is the root cause.

### What is actually wrong

The generic `Water` product is mapped to a **case of 24 × 500 mL San Pellegrino sparkling water**,
with **conversionRatio 1**, which tells Margin Edge that **one case = one gallon**. It is
**12 L = 3.17 gallons**. So there are two stacked errors:

1. **Wrong product.** Tap water used in a smoothie liquid mix should not draw its cost from a
   sparkling-water case at all. Cleveland gets this right.
2. **Wrong conversion.** Even if the sparkling water were correct, the true rate is
   $49.10 ÷ 3.17 gal = **$15.49/gal**, not $49.10/gal — a further 3.17× overstatement.

### Cleveland — correct

- `Get_vendor_items_by_product` → **`"vendorItems": []`. No vendor item.**
- Price history: **22 points, all $0.00** — 2022-03-07, then 2026-03-28 through 2026-07-05 (20
  entries across Mar–Jul 2026).

### Fix

Unlink vendor item **GW115 / centralVendorItemId 5972073** from product 177716372 at Columbus and
map it to a sparkling-water product instead. Columbus's `Water` then falls to $0.00, matching
Cleveland.

### Recipes affected

**Verified affected:** Being Brigid Liquid Mix (110 FLUID_OUNCE line, **$42.20**). A second line at
32 fl oz ($12.28) was reported in the flag but I did not identify which recipe carries it.

**I did not scan all 2,268 recipes and cannot give a count.** Note this does not change the action:
the fault is at the *product* level, so one fix corrects every recipe at once, whatever the count.

---

## Flag 9 — Peanut butter powder

**Product 786552225 · `Peanut Butter, Powder` · report-by unit `1.00 OUNCE`**

### Columbus

- `Get_vendor_items_by_product` (166233400) → **`"vendorItems": []`. Empty.**
- `Get_product_price_history` (166233400, **startDate 2020-01-01**) → **`"priceHistory": []`.
  Completely empty, not just the 12-month window.**

### Cleveland

- `Get_vendor_items_by_product` (166232982) → **`"vendorItems": []`. Also empty.**
- `Get_product_price_history` (166232982, startDate 2020-01-01) → **one point:**

| Date | Unit | Price |
|---|---|---|
| 2024-12-26 | OUNCE | **$1.36** |
| 2024-12-26 | Tablespoon | $0.45 |

$1.36/oz = **$0.0480/g**.

### Answer

**There is no vendor to find.** This product has **never been mapped to a vendor item at either
unit.** That is the answer to the question as asked.

The Columbus recipe line (Keto Powerhouse Powder, verified: **1,875 g, $78.71**) works out to
$1.19/oz = **$0.0420/g**. That figure:
- has **no price point** at Columbus (empty series back to 2020), and
- **does not match** Cleveland's only recorded price ($1.36/oz).

**Its origin is not traceable through the API.** It is a cost with nothing behind it.

### Against the Amazon SKU

| | ME (Columbus) | Amazon (Micro Ingredients, 4 lb / 1,814 g, $28.41) |
|---|---|---|
| $/g | **$0.0420** | **$0.0157** |
| Keto 1,875 g line | **$78.71** | **$29.43** |

**ME overstates the Keto peanut butter line by ~$49.28** — if the Amazon price is the real one.
Since ME has no vendor and no invoice here, **the Amazon SKU is better-evidenced than the Margin
Edge number.** Micro Ingredients Pure Peanut Butter Powder should be added to ME as the vendor
item and the cost rebuilt from it.

---

## Flag 10 — Perfect Keto product

**Product 777254798**

Full product name, verbatim from the API:

> `Perfect keto Nootropic Brain Support Caffeine Free Focus and energy Supplement With Alpha Lipoic Acid L Theanine Gink go Biloba Alpha GPC MCT s Collagen Ketones, Chocolate Drink Mix 15 Servings`

Report-by unit `1.00 EACH`.

### Columbus

- **No vendor items** (`"vendorItems": []`).
- Price history: **one point, 2024-12-11 — $44.99 EACH, $0.17/gram.**
- Recipe line (Keto Powerhouse Powder, verified): **75 g → $12.45.**

### Cleveland — 2 vendor items, both Amazon.com, both Nootropic

| Vendor | Vendor item name | Price | Last ordered |
|---|---|---|---|
| **Amazon.com** | `Perfect Keto Nootropic Brain Support, Caffeine Free Focus and Energy Supplement with Alpha Lipoic Acid, L Theanine, Gink go Biloba, Alpha GPC, MCT's, Collagen, Ketones, Chocolate Drink Mix, 15 Servings` | **$42.74** | **2026-08-10** |
| Amazon.com | `Perfect keto Nootropic Brain Support ... Chocolate Drink Mix 15 Servings` | $44.99 | 2025-05-12 |

Cleveland price history: **19 points, 2024-12-09 → 2026-08-10**, $40.50–$44.99, currently **$42.74**.

### Answer

**Confirmed — and it is stronger than a naming error.** It is not just the *product record* that
says Nootropic; **both Amazon line items are themselves titled "Nootropic Brain Support."** The
actual invoices are for the Nootropic product. So Margin Edge is correctly recording what TownHall
buys, and **the discrepancy is with the slide, not with ME.**

**Vendor: Amazon.com. Current price $42.74.** Columbus has no vendor item — only a stale 2024-12-11
$44.99 price point.

⚠️ Note the cost impact is near zero: 75 g at ME's $0.166/g = **$12.45**; Perfect Keto Base Ketones
on Amazon (243 g, $42.74) is $0.1759/g → **$13.19** for the same 75 g. **A $0.74/batch difference.**
This is purely a question of which product should be in the drink, not a costing question.

---

## Cross-cutting finding: ME's pack-size conversions are wrong on at least four products

This came out of the flags rather than being asked, and it undermines several numbers at once.
Margin Edge stores an `EACH → weight` (or `→ volume`) factor per product, and it does **not** match
the packs actually being bought:

| Product | ID | ME assumes | Vendor items actually say | Effect |
|---|---|---|---|---|
| Chocolate Collagen | 171721217 | 19.3 oz | 17.6 oz / ~14.1 oz / 42.3 oz (three different packs on one `EACH`) | per-gram cost unreliable at **both** units |
| Vanilla Collagen | 176423390 | 19.3 oz | **10.6 oz** (Vital Proteins) | **understated 1.82×** (~$54/cycle) |
| Sea Moss Irish | 965859033 | 8.0 oz | **1 LB** (Nutricost) | **overstated 2×** (~$0.85/batch) |
| Water | 177716372 | 1 case = 1 gallon | 24 × 500 mL = 3.17 gal | **overstated 3.17×**, on top of being the wrong product entirely |
| Cocoa Powder | 171723988 | 2 lb (from a 0.5 ratio) | pack weight **not recorded** | unknown; verify the Whole Foods bag |

**Implication for the order guide:** per-gram costs coming out of Margin Edge cannot be taken at
face value for these lines. The *invoice prices* (price per EACH, per POUND) are reliable — they
come from real invoices. It is the **unit conversions layered on top** that are wrong. Where the
order guide needs $/g, derive it from `pack price ÷ real pack weight`, not from ME's per-ounce or
per-gram figures.

---

## Corrections to `margin-edge-reconciliation.md`

Two statements in the existing reconciliation are contradicted by this round of queries:

1. **"Both prices were last updated 2025-09-29 — exactly 12 months ago"** (chocolate collagen).
   Not correct. **Columbus: 2022-02-18** (one point, ever). **Cleveland: 2025-09-25.** Columbus is
   4.5 years stale, not 1 year, and has no vendor item at all.
2. **"ME's Keto number understates chocolate collagen"** — still true, but the correction is larger
   and less certain than stated, because the 19.3 oz basis behind $0.1037/g is itself wrong.

---

## Still needs Taylor's decision

**Out of scope for Margin Edge — listed per the brief:**

1. Round colostrum 100 g → 96 g?
2. Round peanut butter 1,875 g → 1,814 g?
3. Being Brigid flax: 35 g (slide) or 135 g (ME)? *(ME's 135 g confirmed again in this round —
   recipe 327175351, ingredient 1356619, 135 GRAM, $2.37.)*
4. Batch frequency per location.
5. Split vs. duplicate ordering across the two sites.
6. Coconut sugar pack-vs-unit pricing (Amazon, not in ME).
7. Vanilla bean paste pack format (Amazon, not in ME).

**New decisions surfaced by this research:**

8. **Matcha: culinary or ceremonial?** ME says the kitchen buys Amazon **Culinary Grade** 2 lb at
   $0.0474/g. Santé CoffeeHouse **Ceremonial** is $0.297/g. **$13.48/batch** difference on Being
   Brigid. Either the Santé order is for something else (retail tin? matcha latte?) or the recipe
   is being made with the wrong matcha. **Data can't settle this — it's a product-quality call.**
9. **Vanilla collagen: Vital Proteins or Orgain?** ME buys Vital Proteins Collagen Peptides
   ($0.0930/g true). Orgain Keto Collagen w/ MCT is $0.0706/g. **Different formulations** (Orgain
   has MCT oil); ~$29/cycle. Spec question.
10. **Perfect Keto: Nootropic or Base Ketones?** The Amazon invoices say **Nootropic**. The slide
    says **Base Ketones**. Cost difference is negligible ($0.74/batch) so this is purely "which
    product belongs in the drink."
11. **Cocoa SKU going forward.** Columbus's Whole Foods source hasn't been bought since May 2024;
    Cleveland uses Anthony's Organic 5 lb on Amazon at $49.99. Standardize on one? *(Low stakes —
    ~$2/batch either way.)*

**Data fixes — no decision needed, just someone in Margin Edge:**

- **Unlink San Pellegrino (GW115) from the generic `Water` product at Columbus.** Worth $42.20 on
  every affected recipe.
- **Reprice / re-map chocolate collagen at Columbus.** Worth ~$163/batch on Longevity. Columbus has
  no vendor item at all — one needs creating.
- **Fix the vanilla collagen pack conversion** (19.3 oz → 10.6 oz). Costs are understated ~$54/cycle.
- **Fix the sea moss pack conversion** (8 oz → 16 oz). Costs are overstated ~$0.85/batch.
- **Add a vendor item for peanut butter powder.** It has none at either unit and its $78.71 is
  untraceable.
- **Reprice matcha at Cleveland** (last touched 2022-02-07) and **chai at Cleveland** (2023-05-19).

---

*All figures above were read from Margin Edge on 2026-09-29 via read-only `Get_*` calls. No writes
were attempted. Product IDs and units queried are cited inline so each number can be re-pulled.*
