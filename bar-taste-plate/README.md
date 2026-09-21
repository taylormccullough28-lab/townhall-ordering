# Bar Taste Plate — Spring / Summer 2026

`BAR_TASTE_PLATE_SPRING-SUMMER-2026.xlsx` is the daily bar count sheet. It replaces the
single 73-row sheet with four short pages, each one printable on a single sheet of paper.

| Tab | Who fills it out | What it covers |
|---|---|---|
| 1. Batches & Mixers | Bartender | Cocktail products/batches + juices & mixers |
| 2. Fresh & Garnish | Barback | Limes/lemons counted, garnish + dry goods status |
| 3. Bar Tools | Bartender | Jiggers, stir spoons, hand strainers, muddlers, scraper, strainers, double strainers |
| 4. Setup & Comms | Bartender | Bar set-up walk, daily communication, sign-off |

## How it works

- **Yellow cells are the only cells anyone types in.** Everything else is a label or a formula.
- **NEED is automatic** — `PAR − ON HAND`, floored at zero. It turns gold the moment you're short,
  so the order list is whatever is highlighted.
- **Drop-downs everywhere** instead of free typing: `OK / LOW / 86`, `YES / NO`,
  `OK / DIRTY / BROKEN / MISSING`.
- **Date, shift and name are entered once** on tab 1 and carry through tabs 2–4.
- A `NO` on a set-up line or an `86` on a product turns red on its own.

## Adjusting the lists

The workbook is generated, so item and PAR changes go in the script, not the spreadsheet —
that way the formatting, formulas, drop-downs and print setup can't drift.

1. Edit the lists at the top of `build_taste_plate.py` (`BATCHES`, `MIXERS`, `FRESH_COUNT`,
   `FRESH_YN`, `TOOLS`, `SETUP`).
2. Rebuild and recalculate:

   ```
   python3 bar-taste-plate/build_taste_plate.py
   python3 <xlsx-skill>/scripts/recalc.py bar-taste-plate/BAR_TASTE_PLATE_SPRING-SUMMER-2026.xlsx 300
   ```

## Open item

Bar tool PARs are intentionally blank — the original sheet had no tool counts to carry over.
Set them once with the bar lead (per well plus back-ups) and the NEED column handles the rest.
