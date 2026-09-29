# Margin Edge Reconciliation

Compares the Amazon-screenshot costing built in this repo against **Margin Edge (TownHall –
Columbus, unit 166233400)**, queried 2026-09-29.

**Headline: Margin Edge already has all four powder mixes costed as recipes.** This exercise
independently rebuilt something that exists. The value of the rebuild is that it **surfaces four
concrete errors in the Margin Edge records** and shows where retail pricing diverges from what
TownHall actually pays.

| Recipe | Margin Edge ID | ME cost | This repo | Δ |
|---|---|---|---|---|
| Longevity Powder Mix | 973651246 | **$529.76** / 3,700 g | $428.74 | **+$101.02** |
| Strawberry Skin Powder | 973657060 | **$223.92** / 3,314 g | $253.77 | −$29.85 |
| Being Brigid Powder Mix | 327175351 | **$98.16** / 3,433 g | $129.49 | −$31.33 |
| Keto Powerhouse Powder | 329621048 | **$110.73** / *"1 SERVING"* | $110.49 | +$0.24 ⚠️ |

The Keto match is **coincidence** — two large offsetting errors, see §2.

---

## 1. Questions Margin Edge answered outright

**✅ Strawberry's "Vanilla Collagen Creamer" is not a creamer.** ME uses the *same*
`Powder, Collagen Peptides Protein, Vanilla` as Being Brigid — 400 g in Strawberry, 900 g in Being
Brigid. **One SKU, 1,300 g total.** The "creamer" wording on the slide is loose.

**✅ Keto's cacao powder exists.** ME carries `Spice, Cocoa Powder` at $1.57 / 100 g. It's a
food-category product already in the system — no new sourcing needed. Confirms the cacao nibs really
are cafe-only.

**✅ Cinnamon is costed, not free.** ME prices Longevity's 50 g at $0.76. "Kitchen carries it" means
no separate order line, but it is not zero cost.

**✅ The Pt. 1 / Pt. 2 structure exists.** Each smoothie is built from four component recipes:

| Component | Longevity | Strawberry Skin | Being Brigid |
|---|---|---|---|
| Powder Mix | $529.76 / 3,700 g | $223.92 / 3,314 g | $98.16 / 3,433 g |
| Liquid Mix | $16.77 / gallon | $5.72 / gallon | $53.75 / 4 qt |
| Frozen Bag | $7.39 | $1.58 | $1.86 |
| Fresh Bag | — | — | $0.31 |
| **Finished smoothie** | **$12.86** | **$3.48** | — |

So the unassigned almond milk / MCT oil / oat creamer belong to the **Liquid Mix** recipes. Those are
the missing slides.

---

## 2. Errors found in Margin Edge

**⚠️ Keto — chocolate collagen entered as `1 TABLESPOON`, should be 450 g.**
ME line: `Powder, Collagen Peptides Protein, Chocolate — 1 TABLESPOON — $0.90`.
The slide says **450 g**. At ME's own $0.1037/g that line should be **~$46.67**, not $0.90.
**Keto Powerhouse Powder is understated by roughly $46.** It only appears to match this repo's
number because it is simultaneously overstated on peanut butter (below).

**⚠️ Keto — yield unit is `1 SERVING`, should be 3,850 GRAM.**
Every other powder mix yields in grams. This one can't produce a valid per-gram cost.

**⚠️ Keto — the ketone product doesn't match the slide.**
ME uses **Perfect Keto *Nootropic* Brain Support**; the slide says **BHB Ketone Powder Chocolate**
(Perfect Keto *Base Ketones*). Two different products at a similar price. One of the two is wrong.

**⚠️ Being Brigid — flax quantity disagrees.**
ME: **135 g**. Slide: **35 g**. A 100 g difference.
Also, ME's stated yield (3,433 g) doesn't equal the sum of its own ingredient lines (**3,443 g**).

**⚠️ Peanut butter powder — cost with no price data behind it.**
ME prices 1,875 g at **$78.71** ($0.042/g). `Get_product_price_history` for that product returns
**an empty series** — no purchase in the last 12 months. The live Micro Ingredients SKU is
**$0.0157/g**, so ME overstates this line by **~$49**.

---

## 3. Where retail ≠ what TownHall actually pays

Margin Edge reflects real invoices across foodservice vendors; the Amazon screenshots are retail.
Neither is automatically right, but the gaps are large and one-directional per item:

| Ingredient | This repo (Amazon) | Margin Edge | ME is |
|---|---|---|---|
| Chia Seed | $0.0154/g ($0.44/oz) | **$0.00635/g ($0.18/oz)** | **2.4× cheaper** — purchased regularly, last 2026-09-08 |
| Matcha | $0.2970/g (Santé direct) | **$0.0474/g** | **6× cheaper** — ME uses a generic `Powder, Matcha Green Tea`, not Santé |
| Monkfruit | $0.0359/g | $0.0176/g | 2× cheaper |
| Dragon Fruit | $0.0895/g | $0.0761/g | 15% cheaper |
| Vanilla Collagen | $0.0706/g | $0.0511/g | 28% cheaper |
| **Chocolate Collagen** | $0.0706/g ($2.00/oz) | **$0.1037/g ($2.94/oz)** | **47% MORE** |
| **Peanut Butter Powder** | $0.0157/g | **$0.042/g** | **2.7× MORE** (no recent price data) |
| Colostrum, Spirulina, Hyaluronic, Allulose, Mesquite | — | — | **identical** ✅ |

> **The two matcha lines are probably different products.** ME's is a generic matcha at $0.047/g;
> the Santé CoffeeHouse Ceremonial is $0.297/g. Ceremonial-grade matcha at 6× the price is a real
> choice — but if Being Brigid is *supposed* to use Santé, ME is understating it by ~$13.50/batch.
> If it's supposed to use the generic, the Santé order isn't for this recipe.

---

## 4. What this means for the order guide

1. **Margin Edge is the system of record and should drive the order guide**, not screenshots. It has
   vendors, pack sizes, real invoice prices, price history, and both locations.
2. **Fix the four ME errors first** — Keto's collagen quantity and yield unit, Being Brigid's flax,
   and the peanut butter cost. Until then ME's Keto number is meaningless.
3. **The Amazon work is still worth keeping** as a price check. It found the ME errors, and it shows
   chocolate collagen and peanut butter powder are cheaper on Amazon than what ME is recording.
4. **Chocolate collagen is the one to act on.** It's 3,000 g of Longevity at $0.1037/g in ME vs
   $0.0706/g on Amazon — **~$99/batch** difference on the single largest line in the program.

## 5. Not yet checked

- TownHall – **Cleveland** (unit 166232982) — recipes may differ from Columbus
- Vendor and pack-size detail per product (`Get_vendor_items`) — needed for true order quantities
- Cocktail and cafe recipes
- Whether the `- RB` / `- TH 2.26 CC` / `Test Equip` recipe variants are live or historical

---

# Part 2 — Columbus vs. Cleveland

Cleveland is unit **166232982**, Columbus **166233400**. Queried 2026-09-29.

**The recipes are identical.** Same recipe IDs, same ingredient lines, same quantities at both units.
Every cost difference below comes from **product pricing**, not from different formulations.

| Recipe | Columbus | Cleveland | Δ | Ratio |
|---|---|---|---|---|
| **Longevity Smoothie** | **$12.86** | **$6.41** | +$6.45 | **2.01×** |
| **Being Brigid** | **$7.28** | **$3.83** | +$3.45 | **1.90×** |
| **Keto Powerhouse Smoothie** | **$4.60** | **$2.54** | +$2.06 | **1.81×** |
| Strawberry Skin Renewal | $3.48 | $3.82 | −$0.34 | 0.91× |
| — | | | | |
| Longevity Powder Mix | $529.76 | $374.45 | +$155.31 | 1.41× |
| Being Brigid Powder Mix | $98.16 | $86.26 | +$11.90 | 1.14× |
| Strawberry Skin Powder | $223.92 | $232.38 | −$8.46 | 0.96× |
| Keto Powerhouse Powder | $110.73 | $123.71 | −$12.98 | 0.90× |
| **Being Brigid Liquid Mix** | **$53.75** | **$12.16** | +$41.59 | **4.42×** |
| **Longevity Frozen Bag** | **$7.39** | **$1.66** | +$5.73 | **4.45×** |
| Longevity Liquid Mix | $16.77 | $17.29 | −$0.52 | 0.97× |
| Strawberry Skin Liquid Mix | $5.72 | $6.51 | −$0.79 | 0.88× |
| Strawberry Skin Frozen Bag | $1.58 | $1.72 | −$0.14 | 0.92× |
| Being Brigid Frozen Bag | $1.86 | $1.63 | +$0.23 | 1.14× |

**Three of the four smoothies cost roughly double at Columbus.** Two root causes account for nearly
all of it, and both are verified below.

---

## Root cause 1 — Columbus pays 2.1× for chocolate collagen

Same product (`companyConceptProductId 171721217`), same pack size, same last-priced date:

| | Columbus | Cleveland |
|---|---|---|
| Price EACH | **$56.76** | **$26.99** |
| Per ounce | **$2.94** | **$1.40** |
| Implied pack | 19.3 oz | 19.3 oz |
| Last priced | 2025-09-29 | 2025-09-29 |

Effect on Longevity Powder Mix (identical 3,000 g line):

| Line | Qty | Columbus | Cleveland | Δ |
|---|---|---|---|---|
| Kion Colostrum | 100 g | $57.24 | $57.24 | — |
| Creatine | 250 g | $24.25 | $26.17 | −$1.92 |
| **Chocolate Collagen** | 3,000 g | **$311.22** | **$147.98** | **+$163.24** |
| Blue Spirulina | 300 g | $136.29 | $142.29 | −$6.00 |
| Cinnamon | 50 g | $0.76 | $0.76 | — |
| **Total** | | **$529.76** | **$374.44** | **+$155.32** |

One line explains the entire Longevity gap. For reference, the Amazon Orgain Keto Collagen is
$2.00/oz — **between** the two, so Cleveland is buying it better than retail and Columbus worse.

> **Both prices were last updated 2025-09-29 — exactly 12 months ago.** Neither unit has repriced
> this product in a year, on the largest line in the program.

## Root cause 2 — Columbus is charging $42.20 for water

`Being Brigid Liquid Mix`, same recipe, same 110 FLUID_OUNCE line, same product
(`177716372`):

| | Columbus | Cleveland |
|---|---|---|
| Water, 110 fl oz | **$42.20** | **$0.00** |
| Coconut Cream, 1 EACH | $2.99 | $3.79 |
| Cashew Butter, 330 g | $8.53 | $8.34 |
| Baja Gold Saline, 8 g | $0.04 | $0.03 |
| **Total** | **$53.75** | **$12.16** |

This is a straight data error. It inflates the Being Brigid Liquid Mix by **$42.20** and is most of
why the finished Being Brigid reads $7.28 at Columbus against $3.83 at Cleveland.

## Root cause 3 — Longevity Frozen Bag, 4.45× (not yet fully traced)

Columbus's bag is $7.39, driven by **Pitaya Foods Organic Coconut Smoothie Packs at $6.52 for 0.5
EACH** (implying $13.04 each). Cleveland's whole bag is $1.66. I read the Columbus ingredient list
but **did not pull Cleveland's**, so I can't yet say whether this is a price gap or a different
line. Worth checking — it's the remaining chunk of the Longevity smoothie difference.

---

## What to do

1. **Reprice chocolate collagen at Columbus.** If Columbus can buy at Cleveland's $26.99, Longevity
   Powder Mix drops **$163/batch**. This is the single largest actionable item found anywhere in
   this project. First question: are both units actually buying the same pack from the same vendor,
   or has Columbus's price simply never been corrected?
2. **Zero out the Columbus water cost.** Pure data fix, worth $42.20 on every Being Brigid Liquid Mix.
3. **Reprice anything last touched 2025-09-29.** Both units' collagen is a year stale; there are
   likely others.
4. **Then re-run this comparison.** Plate costs of $12.86 vs $6.41 for the same drink at two
   locations are not a real operational difference — they're mostly bad data, and menu pricing or
   margin decisions made on the Columbus numbers would be wrong.

## Verified vs. not

**Verified by direct query:** all recipe costs in the table above; Longevity Powder Mix ingredients
at both units; Being Brigid Liquid Mix ingredients at both units; chocolate collagen price history
at both units.

**Not checked:** Cleveland's Longevity Frozen Bag and Keto ingredient lines (the Part 1 errors —
Keto's 1-tablespoon collagen, the servings yield unit, Being Brigid's 135 g flax — sit on shared
recipe IDs and so almost certainly affect both units, but I confirmed them only at Columbus);
vendor and pack-size detail; cocktail and cafe recipes.
