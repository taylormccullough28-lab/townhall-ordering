# TownHall CBUS Labor Analysis — extracted summary data

Category-level extraction of the `Labor Summary` tab from all **26 weekly
TownHall CBUS Labor Analysis workbooks**, 2.1.26 through 8.16.26.

**No employee-level data is included here** — no names, hourly rates, individual
pay or tips. Only job-category rollups, department totals and store sales.

Source workbooks live in Rey Gonzalez's OneDrive at
`Documents/TH CBUS Labor Report/` and remain there untouched. See `INDEX.md` for
the full file list and for the other labor-related files across the org.

## Files

| File | Rows | Contents |
|------|------|----------|
| `labor-trend.csv` | 26 | One row per week — the headline series. Report-week sales, labor dollars, labor %, hours; last-year comparatives; and a corrected labor % where the BOH-salary bug applies. **Start here.** |
| `labor-exec-summary.csv` | 468 | EXECUTIVE SUMMARY block: BOH, FOH, Training, FOH Salary, BOH Salary, OTHER, SUBTOTAL, PAYROLL TAX, TOTAL LABOR |
| `labor-boh-detail.csv` | 278 | BOH block: Cook, Prep, Expo, Dish, Salary, BOH total |
| `labor-foh-detail.csv` | 624 | FOH block: Security, Bar Back, Bartender, Crepe, Cafe, Hostess, Runner, Server, Training, Maintenance, COPS, FOH total |
| `labor-mgmt-detail.csv` | 208 | MGMT block: Bonuses, Comp, Salary, MGMT total |
| `labor-sales.csv` | 52 | Total Net Sales, Net Food Sales, and the third sales line per week |
| `DATA-ISSUES.md` | — | **Read this before using the numbers.** 14 data-quality findings. |
| `INDEX.md` | — | Where every labor file lives across the org |
| `rows.tsv`, `sales.tsv` | — | Raw staging files the CSVs are built from |

## Reading the columns

Each workbook shows two side-by-side blocks. They are labelled confusingly on the
sheet ("LY This Week" / "Last week"), so the CSVs use explicit names:

- **`last_year`** — the same week one year earlier. Feeds from the `LY` section of
  the `BOH Salary` / `FOH Salary` tabs.
- **`report_week`** — the week the file is actually reporting on. Feeds from the
  `TY` section.

The sheet's own Variance column is `report_week − last_year` in percentage points.
It is not extracted; compute it from the two rows.

`pct_sales` is against Total Net Sales and is sound.
**`pct_food_sales` is not reliable** — see issue 5 in `DATA-ISSUES.md`.

Dollar values are whole dollars as displayed. `ERR` in `reg_hrs` marks a `#VALUE!`
cell in the source (2.22.26 only). Blank means the cell was empty. A category
absent from a given week simply has no row for that week.

## The short version of the data issues

1. The `Data` tab (employee detail) is **identical in every workbook** — a stale
   paste, worthless for any week.
2. The report-week BOH salary formula is **broken in 11 straight weeks**
   (5.17.26–8.9.26), inflating reported labor % by 2–4 points in ten of them and
   *understating* 6.7.26 by 9 points.
3. **8.9.26 reuses 7.26.26's sales figures**, so every percentage in that file is
   computed against the wrong denominator.
4. **6.28.26's report-week BOH block is a straight copy of 6.21.26's.**
5. `Net Food Sales` and the carry-out/3rd-party line are frequently copied forward
   rather than updated.
6. Individual bad cells: `132,92` text in 2.22.26; 134 Cook hours in 4.12.26; 689
   Training hours and a duplicated Dish OT figure in 4.26.26; 1,824 Cafe hours in
   6.14.26.

Weeks **5.10.26, 5.24.26 and 5.31.26 have no file** — the series has a three-week
gap in May.
