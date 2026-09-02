# Data quality issues found in the TH CBUS Labor Analysis workbooks

Recorded while extracting the Labor Summary tabs. These are problems in the
source workbooks, not in the extraction.

## 1. The `Data` tab is stale in every workbook

The `Data` tab (employee-level hours, rates, pay and tips) is **byte-identical
across every week checked** — 2.1.26, 2.8.26, 2.15.26, 2.22.26 and 8.16.26 all
carry the same 131 rows with the same hours to 9 decimal places.

It is a paste from one payroll pull that was never refreshed. Nothing on the
`Labor Summary` tab references it (the summary values are typed in by hand or
pull from the `BOH Salary` / `FOH Salary` tabs), so the reported numbers are not
corrupted by it — but the `Data` tab itself is worthless for any week and should
not be used or trusted.

## 2. `#VALUE!` errors in 2.22.26

On `Labor Summary` in **2.22.26**, the report-week Training hours cell holds the
text `132,92` instead of a number. That text propagates through the SUM and
leaves two cells showing `#VALUE!`:

- Report-week **FOH** Reg Hrs (`L8`)
- Report-week **SUBTOTAL** Reg Hrs (`L13`)

Both appear as `ERR` in `rows.tsv`. The dollar figures on those rows are
unaffected. The correct report-week totals are recoverable from elsewhere on the
sheet: FOH detail total = **999 hrs**, and the "Total before Tax" row = **1,542 hrs**.

Fix: replace `132,92` with a single number (likely `132` + `92` = 224, but that
needs confirming against payroll).

## 3. Category rows are not consistent week to week

The BOH block carries an **Expo** row in some weeks (8.16.26) and omits it in
others (2.1.26 through 2.22.26). The FOH variance column also labels a row
`JUICING` where the two data blocks label the same row `Maintenance`.

Rows absent from a given week are simply not present in `rows.tsv` for that week
rather than being recorded as zero.

## 4. Hardcoded values overriding formulas

In 8.16.26, BOH Cook is hardcoded (`C22: =464`, `F22: =405+75`) rather than
derived, and the resulting `% of Sales` of 0.25% is inconsistent with the rest of
that row's figures ($6,525 reg pay). Treat 8.16.26 BOH Cook as suspect.

## 5. Net Food Sales and Carry Out Sales are copy-forwarded, not updated

The sales block at the bottom of `Labor Summary` updates `Total Net Sales` every
week, but `Net Food Sales` and `Carry Out Sales` are frequently carried over
unchanged from the prior week's file:

| Week | LY Net Food | LY Carry Out | RW Net Food | RW Carry Out |
|------|-------------|--------------|-------------|--------------|
| 2.8.26  | 96,971  | 49,165 | 66,748 | 34,296 |
| 2.15.26 | 96,971  | 49,165 | 69,771 | 34,296 |
| 2.22.26 | 105,388 | 49,165 | 75,879 | 37,128 |
| 3.1.26  | 105,388 | 49,165 | 75,879 | 37,128 |

`LY Carry Out` is identical across all four weeks, and 2.22.26 and 3.1.26 share
every food/carry-out figure despite `Total Net Sales` moving from 219,802 to
245,705.

**Consequence:** every `% of Food Sales` column is computed against a denominator
that may belong to a different week. Treat `pct_food_sales` in `rows.tsv` as
unreliable. `pct_sales` (against Total Net Sales) is sound.

## 6. The projections block is stale

The "THIS WEEK PROJECTIONS" panel reads `Wk Starting: 2.9.26` in the 2.8.26,
2.15.26, 2.22.26 and 3.1.26 files alike, with identical targets (Sales $125,000,
Food Sales $65,000, Labor $38,000). It was filled in once and never advanced.
Not extracted into the CSVs.

## 7. Implausible BOH Cook hours in 4.12.26

Report-week BOH **Cook** shows **134 reg hrs against $6,430 reg pay** — an implied
rate of about **$48/hr**, roughly triple every other week in the series (typical:
~350-450 hrs against $5,600-$7,700, i.e. $15-$19/hr).

The 134 flows up into the report-week **BOH total of 348 hrs**, which is far below
every other week (typical 540-730). The dollar figures look normal; the hours look
like a transcription error — plausibly the Dish figure (134) pasted over Cook.

Both the Cook row and the BOH exec-summary row for 4.12.26 report_week should be
treated as wrong on hours and correct on dollars.

## 8. The "Notes / Steps to Remedy" net-sales block goes stale

In 4.12.26 the sales block reports Total Net Sales of 215,089 (LY) and 153,864
(RW) — driven by hardcoded formulas `C59: =220296-5207` and
`E59: =156201-5037+2700` — while the "Notes / Steps to Remedy" block at the bottom
still shows the prior week's 205,174 / 144,380 and a total of 200,390 / 139,588.
The two blocks disagree. The sales block is the one the percentages use; the notes
block is vestigial. Not extracted.

## 9. Two errors in 4.26.26 report week

**Training hours of 689.** Report-week Training shows **689 reg hrs against $752
reg pay** — about $1.09/hr. Every other week in the series runs 0-180 training
hours. The 689 propagates into the report-week **FOH total (1,825 hrs)** and
**SUBTOTAL (2,461 hrs)**, both of which are the highest in the series purely
because of it. Likely a decimal or digit-order error (68.9? 68?).

**Dish OT equal to Dish reg pay.** Report-week BOH Dish shows reg pay $1,657 and
**OT pay $1,657** — the identical figure, giving a total of $3,314 and doubling
Dish's cost. This flows into the report-week BOH total OT of $1,748, far above any
other week (typical $0-$600). Almost certainly the reg-pay cell copied into the
OT column.

Both rows are recorded as they appear in `rows.tsv`. Fixing them would lower the
4.26.26 report-week hours and BOH dollars materially.

## 10. Broken cell reference in 5.17.26 — report-week BOH Salary points at last year

On `Labor Summary` in **5.17.26**, the report-week BOH Salary cell reads

    M25: ='BOH Salary'!B35

`B35` is the **LY** total on the `BOH Salary` tab. Every other week in the series
uses `M25: ='BOH Salary'!B17`, the **TY** total. The result is that the report
week is charged last year's BOH salary.

- Reported report-week BOH Salary: **$12,995** (the LY figure)
- Actual TY figure on the `BOH Salary` tab: **$9,118**
- Overstatement: **$3,877**

That $3,877 flows into report-week BOH ($24,120), SUBTOTAL ($40,050), PAYROLL TAX
(20% of it) and TOTAL LABOR ($48,059) — and into the 32.98% TOTAL LABOR figure,
the highest in the whole series. Corrected, report-week total labor is roughly
$43,400 and about 29.8% of sales.

This is the single largest correctable error found. The `rows.tsv` values are as
reported; treat 5.17.26 report_week as overstated.

## 11. Broken cell reference in 6.7.26 — report-week BOH Salary reads an empty cell

Same cell as issue 10, broken a different way. On `Labor Summary` in **6.7.26**:

    M25: ='BOH Salary'!K35

The `BOH Salary` tab only has columns A-H. **Column K is empty**, so the formula
returns **$0** and the entire report-week BOH salary line disappears.

- Reported report-week BOH Salary: **$0** (0.00% of sales)
- Actual TY figure on the `BOH Salary` tab: **$9,268**
- Understatement: **$9,268**

Everything downstream is understated by that amount plus payroll tax:

| Line | Reported | Should be ~ |
|------|----------|-------------|
| Report-week BOH | $10,224 | $19,492 |
| SUBTOTAL | $26,156 | $35,424 |
| PAYROLL TAX | $5,231 | $7,085 |
| **TOTAL LABOR** | **$31,387 (26.13%)** | **~$42,509 (~35.4%)** |

**This is the largest error in the series.** As reported, 6.7.26 looks like the
cheapest labor week of the year at 26.13%; corrected, it is one of the most
expensive. Any trend line drawn through the reported figures will be wrong at this
point.

Together with issue 10, the `M25` BOH-salary reference is broken in at least two
of 26 weeks and should be checked in every file.

## 12. 6.14.26 — BOH-salary bug again, plus a 1,824-hour Cafe figure

**BOH salary (same bug as issue 10).** `M25: ='BOH Salary'!B35` points at the LY
row again. Reported report-week BOH Salary **$13,095**; the TY figure on the
`BOH Salary` tab is **$9,358**. Overstated by **$3,737**, which flows into
report-week BOH, SUBTOTAL, payroll tax and the 31.90% TOTAL LABOR.

**Cafe hours of 1,824.** The last-year Cafe row is hardcoded `C35: =1824` against
$1,093 of pay — about $0.60/hr. Every other Cafe week runs 135-250 hours. It
inflates last-year FOH to **3,437 hrs** and last-year SUBTOTAL to **4,128 hrs**,
both roughly double any other week. Almost certainly meant to be ~182.

So in 6.14.26 the last-year hours are inflated and the report-week dollars are
inflated, in opposite blocks. Dollar figures elsewhere in the week look normal.

## 13. 6.28.26 report-week BOH block is a copy of 6.21.26

Every report-week BOH detail row in **6.28.26** is identical to **6.21.26**:

| Row | 6.21.26 | 6.28.26 |
|-----|---------|---------|
| Cook | 498 hrs / $7,887 / $7 OT | 498 hrs / $7,887 / $7 OT |
| Prep | 73 / $1,229 / $286 | 73 / $1,229 / $286 |
| Expo | 58 / $880 / $584 | 58 / $880 / $584 |
| Dish | 124 / $1,086 / $0 | 124 / $1,086 / $0 |
| BOH total | 753 hrs | 753 hrs |

The FOH block and the sales figures differ between the two weeks, so this is not
two identical weeks — the BOH block was pasted forward and never updated.
**6.28.26 report-week BOH is not real data.**

The same file also repeats the BOH-salary bug (`M26: ='BOH Salary'!B35`):
reported **$14,008** against a TY figure of **$8,768**, overstated by **$5,240**.
Combined, 6.28.26 shows the highest TOTAL LABOR in the series at 35.43% — a
figure that is not trustworthy.

## 14. 8.9.26 copies its entire last-year block and sales block from 7.26.26

In **8.9.26**, every last-year figure is identical to **7.26.26** — the whole
EXECUTIVE SUMMARY, BOH and FOH last-year columns, down to the odd 110-hour Bar Back
row. So is the whole sales block:

| | 7.26.26 | 8.9.26 |
|---|---------|--------|
| LY Total Net Sales | 175,690 | 175,690 |
| LY Net Food Sales | 93,688 | 93,688 |
| **LW Total Net Sales** | **155,701** | **155,701** |
| LW Net Food Sales | 78,446 | 78,446 |

The `C60` sales formula is the same hardcoded `=180045-4355` in both files.

**This matters more than the other copy-forwards.** The report-week sales figure is
the denominator for every `% of Sales` in the file. 8.9.26's report-week
percentages are computed against 7.26.26's sales, so **every percentage in 8.9.26
is wrong** unless the two weeks genuinely did identical volume.

The report-week FOH block is also near-identical to 7.26.26 — only Security differs
(13 hrs/$252 vs 12/$238). Report-week BOH does differ.

---

# The BOH-salary bug, all weeks

`Labor Summary` pulls report-week BOH salary from the `BOH Salary` tab. The correct
reference is the **TY** total (`B17`). From **5.17.26 through 8.9.26 — eleven
consecutive weeks — it points somewhere else instead.** It is correct again in
8.16.26.

| Week | Formula | Reported | Actual TY | Error |
|------|---------|----------|-----------|-------|
| 2.1.26 – 5.3.26 | `B17` ✅ | — | — | correct |
| 5.17.26 | `B35` (LY) | 12,995 | 9,118 | **+3,877** |
| 6.7.26 | `K35` (empty) | 0 | 9,268 | **−9,268** |
| 6.14.26 | `B35` (LY) | 13,095 | 9,358 | **+3,737** |
| 6.21.26 | `B35` (LY) | 13,395 | 8,768 | **+4,627** |
| 6.28.26 | `B35` (LY) | 14,008 | 8,768 | **+5,240** |
| 7.05.26 | `B35` (LY) | 12,383 | 8,768 | **+3,615** |
| 7.12.26 | `B35` (LY) | 12,615 | 8,414 | **+4,201** |
| 7.19.26 | `B35` (LY) | 12,615 | 8,414 | **+4,201** |
| 7.26.26 | `B35` (LY) | 12,383 | 8,768 | **+3,615** |
| 8.2.26 | `B35` (LY) | 11,272 | 9,018 | **+2,254** |
| 8.9.26 | `B35` (LY) | 12,383 | 8,768 | **+3,615** |
| 8.16.26 | `B17` ✅ | 8,518 | 8,518 | correct |

Each error also moves payroll tax (20%) and TOTAL LABOR. `labor-trend.csv` carries
a `rw_total_labor_pct_corrected` column showing what report-week total labor % would
be with the BOH salary line fixed:

| Week | Reported | Corrected |
|------|----------|-----------|
| 5.17.26 | 32.98% | 29.79% |
| **6.7.26** | **26.13%** | **35.38%** |
| 6.14.26 | 31.90% | 28.97% |
| 6.21.26 | 32.40% | 28.76% |
| 6.28.26 | 35.43% | 30.90% |
| 7.05.26 | 45.89% | 41.57% |
| 7.12.26 | 35.74% | 31.96% |
| 7.19.26 | 33.66% | 29.86% |
| 7.26.26 | 31.87% | 29.08% |
| 8.2.26 | 37.82% | 35.52% |
| 8.9.26 | 31.04% | 28.25% |

**The headline effect:** as reported, labor % looks like it jumped from the low-to-mid
20s in Feb–early May to the low-to-mid 30s from mid-May on. Corrected, it still
rises — but to roughly 29-31%, not 32-36%. And 6.7.26, which reads as the cheapest
week of the summer at 26.13%, is really among the most expensive at ~35%.
