# Bar Taste Plate — Spring / Summer 2026

`BAR_TASTE_PLATE_SPRING-SUMMER-2026.xlsx` is the daily bar count sheet:
**one sheet of paper, printed double-sided.**

The workbook has two tabs because a sheet of paper has two sides:

| Tab | Side | What's on it |
|---|---|---|
| `SIDE 1 - FRONT` | Front | Cocktail batches + juices/mixers (left), fresh + garnish (right) |
| `SIDE 2 - BACK` | Back | Bar tool count + bar set-up walk (left), daily communication + notes + sign-off (right) |

## Printing

File → Print → **Print Entire Workbook**, and turn on double-sided (flip on long edge).
Each tab is set to print as exactly one page, so you get one front-and-back sheet every time.
Don't switch the print setting to "fit to 2 pages" — each side is already sized to its page.

## How it works

- **Yellow cells are the only cells anyone types in.** Everything else is a label or a formula.
- **NEED is automatic** — `PAR − ON HAND`, floored at zero so an over-par count never goes negative.
  It turns gold the moment you're short, so the order list is whatever is highlighted.
- **Drop-downs instead of free typing**: `OK / LOW / 86`, `YES / NO`, `OK / DIRTY / BROKEN / MISSING`.
- **Date, shift and name are typed once** on the front and print across the top of the back.
- A `NO` on a set-up line, an `86` on a product, or a `BROKEN`/`MISSING` tool turns red on its own.
- Bar tools total up "TOOLS SHORT TODAY" so a missing jigger doesn't get lost in the grid.

## Adjusting the lists

The workbook is generated, so item and PAR changes go in the script, not the spreadsheet —
that way the layout, formulas, drop-downs and print setup can't drift.

1. Edit the lists at the top of `build_taste_plate.py` (`BATCHES`, `MIXERS`, `FRESH_COUNT`,
   `FRESH_YN`, `TOOLS`, `SETUP`, `COMMS`).
2. Rebuild and recalculate:

   ```
   python3 bar-taste-plate/build_taste_plate.py
   python3 <xlsx-skill>/scripts/recalc.py bar-taste-plate/BAR_TASTE_PLATE_SPRING-SUMMER-2026.xlsx 120
   ```

Each side holds roughly 24 line items per column before it needs to shrink to fit, so there's
room to add a few cocktails or syrups without the layout changing.

## Open items — pars still to set

Two sets of PAR boxes are blank on purpose and print as yellow fill-ins:

- **The seven new batches** (Channel Orange, Pear Chai, Don't Worry About It Sweetheart,
  Cider Mix, Chai Hard, Pecan Brown Simple, Scarlett Spritz) — no par was given for these yet.
- **Bar tools** — the original sheet had no tool counts to carry over. Set them once with the
  bar lead (per well plus back-ups).

NEED stays blank until both PAR and ON HAND are filled in, so a missing par never reads as
"you're fully stocked." Once a par is set in `build_taste_plate.py` it prints as a fixed
blue number like the rest.
