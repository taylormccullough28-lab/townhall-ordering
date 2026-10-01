# Margin Edge Fix Sheet — Water & Patron Silver

**I could not make these changes.** The Margin Edge connector in this session is **read-only** —
every tool is a `Get_*`, and Margin Edge's own help directory lists no create/update/delete
workflow. These need someone with write access in the Margin Edge UI.

Everything below was verified directly against the API on 2026-10-01, unit
**TownHall – Columbus (166233400)**.

---

## Fix 1 — Water: a case of San Pellegrino is mapped as one gallon

**Product:** `Water` · companyConceptProductId **177716372** · report-by unit **GALLON**

### What the data shows

Product units:

| Packaging | Unit | Qty | Price | Ratio | Role |
|---|---|---|---|---|---|
| Water | **GALLON** | 1 | **$49.10** | 1 | count-by + **report-by** |
| Gram | GRAM | 1 | $0.01 | 0.0002640625 | |

Its only vendor item:

| Vendor | Item code | Item name | Packaging | Price | Conv. ratio | Last ordered |
|---|---|---|---|---|---|---|
| Chefs Warehouse | **GW115** | **San Pellegrino Water Sparkling** | Case / 24 / 500ML Btl | **$49.10** | **1** | 2025-09-19 |

### The error
A **case of 24 × 500 ml San Pellegrino** has been attached to the generic `Water` product with a
conversion ratio of **1**, so Margin Edge believes **one case = one gallon** and values a gallon of
water at **$49.10**.

Reproduces the observed costs exactly:
- Being Brigid Liquid Mix: 110 ÷ 128 × $49.10 = **$42.20** ✓
- Brewed Chai Tea: 32 ÷ 128 × $49.10 = **$12.28** ✓
- Against Doctor's Orders: 15.25 ÷ 128 × $49.10 = **$5.85** ✓

For reference, 24 × 500 ml = 12 L = **3.17 gallons**, so even the ratio itself is wrong by 3.17×.

### Recommended fix
**Detach GW115 (San Pellegrino) from the `Water` product** and give it its own product. The generic
`Water` used as tap water in recipes should carry no vendor item and no cost.

**Cleveland is already configured correctly** — no vendor item on `Water`, and it costs $0.00 in
every recipe. Match Columbus to Cleveland.

> Do **not** simply correct the ratio to 3.17. That would value tap water at $15.49/gal, which is
> still wrong — it would just be wrong by less. San Pellegrino is a purchased beverage and belongs
> on its own product.

### Affected recipes (confirmed so far — there are likely more)
Being Brigid Liquid Mix · Brewed Chai Tea · Against Doctor's Orders #1 - Batch, plus anything built
on them (Pear Chai Tea, Being Brigid finished smoothie).

---

## Fix 2 — Patron Silver: a duplicate unit row costs a bottle at 1/750th

**Product:** `Patron Silver` · companyConceptProductId **220983364** · report-by unit **Bottle (750 ML)**

### The vendor prices are fine
All three vendor items agree at **$47.00 / 750 ml bottle**:

| Vendor | Item code | Price | Last ordered |
|---|---|---|---|
| Arena Liquor LLC | 7984B | $47.00 | **2026-09-03** |
| Arena Wine & Spirits | 7984B | $47.00 | 2024-05-23 |
| CMG – Ethos Internal Transfers | 1349050379 | $47.00 | — |

**So this is not a price problem.** Nothing needs repricing.

### The error is a broken unit row

| # | Packaging | Unit | Qty | Price | Ratio | Role |
|---|---|---|---|---|---|---|
| 1 | Bottle | MILLILITER | 750 | $47.00 | 1 | count-by + report-by ✅ |
| 2 | Patron Silver 750mL | MILLILITER | 750 | $47.00 | 1.000000025 | ✅ |
| 3 | **Bottle** | **BOTTLE** | **1** | **$0.06** | **0.0013333334** | ❌ **BROKEN** |
| 4 | Bottle | BOTTLE | 750 | $47.00 | 1.000000025 | ✅ |

Row 3 declares a `BOTTLE` unit of quantity **1** with ratio **0.0013333334**, which is **1/750**.
So Margin Edge treats one bottle as one seven-hundred-fiftieth of the report-by unit:

**$47.00 × 1/750 = $0.0627 ≈ $0.06**

The `Grapefruit Infused Patron` recipe (recipeId 333473987) calls for **1 BOTTLE** and picks up row 3.

### Recommended fix
**Delete unit row 3** (`Bottle` / BOTTLE / qty 1 / ratio 0.0013333334). Row 4 already defines the
correct BOTTLE unit at qty 750, $47.00, ratio ~1. Once row 3 is gone, the recipe should resolve to
**$47.00**.

### Impact
| Recipe | Now | After fix |
|---|---|---|
| Grapefruit Infused Patron | $0.06 | **~$47.00** |
| At Dawn They Sleep - Batch | $25.48 (34 fl oz) | **~$40.00** |
| At Dawn They Sleep (drink) | $2.25 | higher |

The infusion yields 1 bottle (~25.4 fl oz) and At Dawn They Sleep draws 11.25 fl oz of it, so roughly
$20.80 of real Patron cost is currently missing from that batch.

---

## Verify after fixing

Re-read the two recipes and confirm:
- `Being Brigid Liquid Mix` (327173824) — water line should read **$0.00**, batch total drops from
  $53.75 to about **$11.55**
- `Grapefruit Infused Patron` (333473987) — Patron line should read **~$47.00**

## Still outstanding (not part of this fix)
The four wrong pack conversions — chocolate collagen, vanilla collagen, sea moss, and the Columbus
chocolate-collagen vendor item that does not exist. See `flag-research.md` and
`smoothie-powder-prep/margin-edge-reconciliation.md`.
