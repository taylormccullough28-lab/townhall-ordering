# Test fixtures — ALL SYNTHETIC

**Nothing in this directory is real TownHall data.** Every file here was
written by `build_fixtures.py` to reproduce the *structure* of Toast exports as
documented in `PRD-beverage-ordering.md` ("Appendix: Toast Report Ingest").
None of it came out of Toast, none of it is a real sales week, and no quantity
here should be used to size an order, set a par, or validate a forecast.

Regenerate with:

```
python tests/fixtures/build_fixtures.py
```

## Why these exist

No Toast export was available when the parsers were written — no API access, no
credentials, and the only exports the PRD's authors recovered were from a
different concept in the same Toast account. The fixtures therefore encode the
*documented* structure and, deliberately, its nastiest observed edges.

## What each file is, and the trap it carries

| File | Shape | The trap it exists to catch |
|---|---|---|
| `pmix_full.xlsx` | Multi-sheet PMIX: `Summary`, `All levels`, `Menus`, `Menu groups`, `Items`, `Open items`, `Modifiers`, `Special requests` | `All levels` mixes rollup rows (blank `Type`) with leaf rows (`menuItem`/`openItem`). Counting rollups double-counts every quantity. Also carries a `Total` row, an `openItem` row, and a blank-`Sales Category` liquor SKU (`Bacardi FB`, qty 4). |
| `pmix_variant_subgroup_no_category.xlsx` | Same account, different export options | **No `Sales Category` column anywhere.** Has `Subgroup`, `Avg. price`, `Gross sales`, `Net sales`. Columns are in a *different order*, and the `Items` sheet has `Qty sold` before `Item`. A positional parser reads garbage. `Modifiers` and `Special requests` sheets are absent entirely. |
| `pmix_all_levels_no_type.xlsx` | `All levels` exported without `Type` | Rollups cannot be told from leaves. The parser must refuse the sheet and say so, not quietly double the week. |
| `item_selection_details.csv` | Line-item CSV, observed header verbatim | Two locations in one file; a `TRUE` void; a 01:30 sale that belongs to the *prior* business day; a 04:05 sale that starts the new one; an unmappable item; a trailing totals row with every field blank except `Qty`. |
| `item_selection_details_with_mods.csv` | Line-item CSV, shuffled columns | Column order scrambled, plus `Comp?` and `Modifiers` columns the observed export does not have. Carries Single / Rocks / Double pour modifiers, one sale with no modifier at all (must default to Single), a comp (counted, flagged) and a void (excluded), and one unclassified modifier. |
| `item_selection_history.csv` | Five weeks of timestamped line items ending Sunday 2026-08-30 | Feeds the trailing-4-week weekday baseline and the hourly profile the post-cutoff adjustment prorates against. Quantities follow a fixed weekday shape with deterministic jitter. |
| `catalog/` | A four-file catalog (`vendors`, `products`, `mappings`, `config`) | Vendor windows mirror the real appendix so the days-of-cover assertions test the real calendar. Contacts are placeholders. Unlike the shipped seed catalog, products here have vendors assigned, because the real product-to-distributor mapping lives in a document this repo does not have. |

## What the fixtures deliberately do NOT claim

* **Sales Category values.** `Liquor`, `Bottled Beer`, `NA Beverage`,
  `Bottle Service` and blank are the values observed at a *different* location.
  Short North's actual set is unconfirmed.
* **Modifier data.** No modifier-level export exists in the account. The
  `Modifiers` sheet in `pmix_full.xlsx` is present and empty, exactly as
  observed. The pour modifiers in `item_selection_details_with_mods.csv` are
  invented to exercise the pour logic — Toast's real spelling is unknown.
* **Demand.** The weekday shape and hourly curve in `item_selection_history.csv`
  are made up to be plausible and stable, not measured.
