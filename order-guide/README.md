# TownHall Order Guide

Working files for the prep + ordering guide. Organized **by prep category**, with a shared SKU
tracker per category. A vendor/order-run cross-reference gets built at the end, once the categories
are populated — that way one master order can be assembled from whichever categories are due.

## Structure

| Folder | Contents | Status |
|---|---|---|
| `smoothie-powder-prep/` | 4 powder prep recipes (Strawberry, Longevity, Being Brigid 2.0, Keto 2.0) | 21 of 21 identified; 2 prices open |
| `cocktail-prep/` | Cocktail / bar prep recipes and SKUs | Awaiting recipes |
| `unassigned-skus.md` | Products seen in order history, not yet matched to a recipe | 15 items |

## Files

- `smoothie-powder-prep/ingredient-breakdown.md` — shared vs. recipe-specific ingredients, master
  ingredient list, shared prep method
- `smoothie-powder-prep/skus-and-order-quantities.md` — confirmed SKUs, grams → units to order,
  per-batch cost, open questions
- `unassigned-skus.md` — holding pen; items move out to a category once their recipe lands

## Vendors

Sourcing is **not single-vendor** — the master order will need to split by supplier:

| Vendor | Covers | Notes |
|---|---|---|
| Amazon Business | Most powder prep SKUs | ⚠️ **Two ship-to addresses seen**: Townhall – Columbus 43215 and Townhall – Cleveland 44113. Confirm whether prep runs at both sites — if so, quantities are per location. Subscribe & Save available on several lines |
| Hillcrest Foods | Allulose powder | Pack size, price, and lead time still needed |
| Sante (direct or distributor?) | Sante Matcha, 250 g | Vendor route and price still needed |
| In-house / kitchen stock | Cinnamon | Pull-from-stock, no order line |

## Conventions

- Every ingredient is tracked in **grams** (recipes are in grams); units to order are computed from
  the SKU's net weight, always rounded **up** to whole units.
- "Ingredient cost" = cost of the grams actually consumed. "Unit cost" = cash outlay for whole
  packages. They differ wherever a package spans multiple batches.
- Prices are point-in-time from Amazon Business (ship to Townhall – Columbus 43215) and are dated
  where captured. Re-verify before placing a large order.
- Anything ambiguous gets a ⚠️ flag and an entry in that file's open-questions section rather than a
  silent assumption.
- **Not every ingredient is an order line.** Items the kitchen already carries in stock (e.g. cinnamon)
  are marked *carried in-house* — they stay on the **prep** guide as a pull-from-stock step but are
  excluded from the **order** guide. Flag these as they surface so the order guide doesn't
  double-order what's already on the shelf.
