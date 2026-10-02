# Catalog completeness audit

**Date:** 2026-09-14 · **Source:** MarginEdge Purchase Report, TownHall Columbus, 2026-07-20 → 2026-08-28 (5.7 weeks)

**Short answer: the catalog is not complete, and this report structurally cannot complete it.** Read this before writing a PRD off the current data.

---

## What we have

| | Count |
|---|---|
| Beverage product lines in the window | **264** |
| Products named in `TH_ORDER_GUIDE.docx` | **53** |
| Guide products confirmed in the window | **44 of 53** |

So the order guide covers roughly **20% of what is actually purchased**. It is a curated core list, not a catalog. Any system built only from the guide is blind to four-fifths of beverage spend.

---

## Gap 1 — Naming. The biggest problem, and it is silent.

The order guide uses **bar shorthand**. MarginEdge uses **full product names**. These are the same product:

| Guide says | MarginEdge says |
|---|---|
| `CBC` | `Columbus Brewing Company Bodhi Keg (50L)` |
| `Mango Cart` | `Golden Road Mango Keg (1/2BBL)` |
| `Suncruiser` | `Sun Cruiser Classic Iced Tea Vodka 12OZ Can` |
| `Garage Beer Lime` | `Garage Lime Keg (1/2BBL)` |
| `Elvis Juice` | `Brew Dog Elvis Juice IPA Keg (1/2BBL)` |
| `Hazy Little Thing` | `Sierra Nevada Hazy Little Thing Keg (1/2BBL)` |
| `Mr. Boston Triple Sec` | `Mr Boston Triple Sec 1L` |

A naive name match reports these as missing products. They are not missing — they are **unmapped**. This is the single largest source of silent error in the whole system: it produces confident, wrong answers rather than visible failures.

**Implication for the PRD:** the mapping layer is not a nice-to-have, it is the product. Budget it as the largest work item and give it a named owner.

---

## Gap 2 — Anything ordered less often than every 5.7 weeks is invisible

Verified absent from this window, cross-checked by substring rather than fuzzy match:

| Product | Vendor | Why it is probably absent |
|---|---|---|
| **Veuve Brut** | Southern Glazer's | Bottle service — lumpy |
| **Veuve Rosé** | Southern Glazer's | Bottle service — lumpy |
| **Ace of Spades** | Southern Glazer's | Guide already flags "not ordered frequently" |
| **Dom Pérignon** | Southern Glazer's | Guide already flags "not ordered frequently" |
| **Brew AF Mix N/A** | Superior | Slow mover |
| **Cheetah** | Superior | Rotating keg, out of rotation |
| **Busch Light** | Columbus Dist. | In the 2026 draft lineup but not bought this window |
| **Happy Hour Red & White** | Heidelberg | Guide says "order a case when needed" |

**The entire champagne program is invisible in this window.** The only match for "champagne" in 803 rows is *Champagne Vinegar*. Veuve, Ace of Spades and Dom Pérignon — the highest-dollar SKUs in the building — do not appear at all.

This is exactly the failure mode the PRD predicts for bottle service: lumpy, event-driven, and impossible to forecast from a trailing average. A five-week window doesn't just under-weight them, it **erases them**, and a catalog seeded from this data would not know they exist.

---

## Gap 3 — No vendor, anywhere

The Purchase Report has **no vendor column**. Every one of the 264 products carries `vendor: null` and `vendor_confidence: unconfirmed`. Per-vendor order sheets are empty by design until this is filled.

## Gap 4 — No dates

The report is aggregated over the whole period. There is no order date, no invoice number, no reorder rhythm — and no way to settle which order guide is current from this data.

---

## What to pull from MarginEdge to close this

In priority order. Items 1 and 2 are what a complete catalog actually requires.

1. **Product / item catalog export** — *every active product*, not just what was purchased in a window. This is the fix for Gap 2. A purchase report can only ever show what moved.
2. **Vendor items export, or the auto-generated Order Guides per vendor** — closes Gap 3, and per MarginEdge's documentation these carry SKU, pack size and last-paid price.
3. **Purchase report for a full 12 months** — catches seasonal and slow-moving products the 5.7-week window misses. Cheaper than item 1 if the catalog export is not available.
4. **Invoice-level detail with dates** — closes Gap 4 and gives reorder rhythm.

---

## Recommendation before sharing a PRD with other operators

The current catalog is **good enough to prove the concept and wrong to standardize on**. Specifically:

- **Do share** the ordering logic, the vendor windows, the depletion math, the keg-credit finding, and the café lead-time analysis. Those hold.
- **Do not present the 264-product catalog as the product list.** It is one location's 5.7-week purchase window with no vendors attached, missing the entire champagne program.
- **Do flag the naming problem prominently.** Any operator rolling this out at their own location hits it immediately, and it is worse at scale — every location has its own shorthand.
- **State the window.** A reader who assumes the catalog is complete will conclude the bar does not sell champagne.
