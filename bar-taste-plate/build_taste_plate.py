"""
Build the TownHall BAR TASTE PLATE - one sheet of paper, printed double-sided.

Two tabs, one per physical side: each is set to print as exactly one page.
Print the whole workbook double-sided and you get one front-and-back sheet.

    python3 bar-taste-plate/build_taste_plate.py
    python3 <xlsx-skill>/scripts/recalc.py bar-taste-plate/BAR_TASTE_PLATE_SPRING-SUMMER-2026.xlsx

SIDE 1  count & order   - batches + mixers (left), fresh & garnish (right)
SIDE 2  tools & set-up  - bar tools + set-up walk (left), communication (right)

Everything a bartender/barback fills in is a yellow cell. NEED is a formula
(PAR minus ON HAND) - never type in it. To change the sheet, edit the lists
below and rebuild; the layout, formulas and print setup take care of themselves.
"""

import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.comments import Comment

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "BAR_TASTE_PLATE_SPRING-SUMMER-2026.xlsx")

# ---------------------------------------------------------------- content ---
# PARs carried over from the original BAR_TASTE_PLATE_SPRING-SUMMER2026.xlsx.

BATCHES = [
    ("Green Goddess Biz",            8, "BTL"),
    ("Spicy Cucumber Biz",           8, "BTL"),
    ("Say Less",                     6, "BTL"),
    ("Light My Fire 2.0 Biz",        6, "BTL"),
    ("Turmeric Juice (LMF 2.0) *",   6, "BTL"),
    ("No New Friends Biz",           6, "BTL"),
    ("Hot Girl Simmer Biz",          6, "BTL"),
    ("Alter Ego Biz",                6, "BTL"),
    ("Coconut Blue Spirulina",       6, "BTL"),
    ("Not Your Average Spritz",      6, "BTL"),
    ("Strawberry Allulose",          6, "BTL"),
    ("Tart Cherry Allulose",         3, "BTL"),
    ("Nitro Espresso Martini",       1, "CMB"),
]
BATCH_NOTE = "* Turmeric Juice is for Light My Fire 2.0 - NOT the wellness shot."

MIXERS = [
    ("Pineapple Juice",   4, "BTL"),
    ("Orange Juice",      4, "BTL"),
    ("Grapefruit Juice",  4, "BTL"),
    ("Watermelon Juice",  6, "BTL"),
    ("House Grenadine",   2, "BTL"),
    ("Olive Juice",       1, "BTL"),
    ("Simple Syrup",      6, "BTL"),
    ("Lemon Juice",       6, "BTL"),
    ("Lime Juice",        6, "BTL"),
    ("Bloody Mary Mix",   6, "BTL"),
    ("Espresso",          4, "BTL"),
]

FRESH_COUNT = [("Limes", 8, "PAN"), ("Lemons", 8, "PAN")]

FRESH_YN = [
    "Olives", "Mint", "Parsley", "Basil", "Tarragon",
    "Dehydrated Strawberries", "Dried Calendula Flowers", "Thai Chili",
    "Hibiscus Leaves", "Cherries", "Espresso Beans", "Dried Dragonfruit",
    "Dragon Fruit Powder", "Electrolyte Salt", "Jalapenos", "Salt", "Sugar",
    "Angostura Bitters",
]

TOOLS = ["Jiggers", "Stir Spoons", "Hand Strainers", "Muddlers",
         "Scraper", "Strainers", "Double Strainers"]

SETUP = [
    ("Glasses",         "Spot check - clean, no chips"),
    ("Coolers",         "Stocked + clean"),
    ("Silverware",      "Stocked / full"),
    ("Napkins",         "Stocked"),
    ("Side Plates",     "Clean + stocked"),
    ("Sriracha",        "Wiped clean, enough on hand"),
    ("Salt and Pepper", "Full + wiped clean"),
    ("Register Paper",  "Back-up at each printer"),
    ("Ice Scoops",      "In place"),
    ("Shaker Tins",     "In place at every well"),
    ("Pens",            "Stocked"),
    ("Crowlers",        "Labeled + stocked"),
    ("Crowler Machine", "Cleaned"),
    ("Sharpies",        "By crowler machine"),
    ("Wine Pourer",     "In place"),
    ("Wine Opener",     "In place"),
]

COMMS = [
    ("New drafts poured through at every beer tower?", ["YES", "NO"], "NO"),
    ("8 oz pour beer taps marked?",                    ["YES", "NO"], "NO"),
    ("Anything 86'd today?  (list it below)",          ["NO", "YES"], "YES"),
]

# ---------------------------------------------------------------- styling ---
FONT = "Arial"
NAVY = "1F3A5F"
TEAL = "2E6F6A"
GOLD = "FFD966"
REDF = "F8CBAD"
REDT = "9C0006"
GREY = "EDEFF2"
INPUT = PatternFill("solid", fgColor="FFFDE7")

thin = Side(style="thin", color="B7BEC8")
med = Side(style="medium", color=NAVY)
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

LEFT_C, GUT_C, RIGHT_C = 1, 6, 7        # A..E | F | G..K
LAST_C = 11
WIDTHS = {1: 21.5, 2: 6.2, 3: 6.2, 4: 6.2, 5: 7.0, 6: 1.2,
          7: 21.5, 8: 6.2, 9: 6.2, 10: 6.2, 11: 7.0}


def f(size=10, bold=False, color="000000", italic=False):
    return Font(name=FONT, size=size, bold=bold, color=color, italic=italic)


CTR = Alignment(horizontal="center", vertical="center")
LFT = Alignment(horizontal="left", vertical="center", indent=1)
WRP = Alignment(horizontal="left", vertical="center", wrap_text=True, indent=1)


def L(col):
    return get_column_letter(col)


def span(ws, row, c0, c1):
    ws.merge_cells(start_row=row, start_column=c0, end_row=row, end_column=c1)
    return ws.cell(row=row, column=c0)


def title(ws, row, text):
    c = span(ws, row, 1, LAST_C)
    c.value = text
    c.font = f(14, True, "FFFFFF")
    c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 26
    for col in range(1, LAST_C + 1):
        ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor=NAVY)


def subtitle(ws, row, text):
    c = span(ws, row, 1, LAST_C)
    c.value = text
    c.font = f(10, True, "FFFFFF")
    c.fill = PatternFill("solid", fgColor=TEAL)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
    ws.row_dimensions[row].height = 19
    for col in range(1, LAST_C + 1):
        ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor=TEAL)


def band(ws, row, c0, c1, text):
    c = span(ws, row, c0, c1)
    c.value = text
    c.font = f(9.5, True, NAVY)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    for col in range(c0, c1 + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = PatternFill("solid", fgColor=GREY)
        cell.border = Border(top=med, bottom=thin, left=thin, right=thin)
    ws.row_dimensions[row].height = 19


def col_header(ws, row, c0, labels):
    for i, text in enumerate(labels):
        c = ws.cell(row=row, column=c0 + i, value=text)
        c.font = f(8.5, True, "FFFFFF")
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = Border(left=thin, right=thin, top=med, bottom=med)
    ws.row_dimensions[row].height = 24


def count_row(ws, row, c0, name, par, unit):
    """ITEM | PAR | HAVE | NEED | STATUS  - only HAVE and STATUS get typed in."""
    it = ws.cell(row=row, column=c0, value=name)
    it.font = f(9.5)
    it.alignment = LFT

    p = ws.cell(row=row, column=c0 + 1, value=par)
    p.number_format = f'0" {unit}"'
    p.font = f(9.5, True, "0000FF")
    p.alignment = CTR

    have = ws.cell(row=row, column=c0 + 2)
    have.fill = INPUT
    have.font = f(9.5, True)
    have.alignment = CTR

    hl, pl = L(c0 + 2), L(c0 + 1)
    need = ws.cell(row=row, column=c0 + 3,
                   value=f'=IF({hl}{row}="","",MAX(0,{pl}{row}-{hl}{row}))')
    need.font = f(9.5, True)
    need.alignment = CTR

    st = ws.cell(row=row, column=c0 + 4)
    st.fill = INPUT
    st.font = f(9.5)
    st.alignment = CTR

    for col in range(c0, c0 + 5):
        ws.cell(row=row, column=col).border = BOX
    ws.row_dimensions[row].height = 20


def status_row(ws, row, c0, name):
    """ITEM | (no count) | STATUS - for garnish and dry goods."""
    it = ws.cell(row=row, column=c0, value=name)
    it.font = f(9.5)
    it.alignment = LFT
    dash = span(ws, row, c0 + 1, c0 + 3)
    dash.value = "-"
    dash.font = f(9, color="C2C8D2")
    dash.alignment = CTR
    st = ws.cell(row=row, column=c0 + 4)
    st.fill = INPUT
    st.font = f(9.5)
    st.alignment = CTR
    for col in range(c0, c0 + 5):
        ws.cell(row=row, column=col).border = BOX
    ws.row_dimensions[row].height = 20


def note(ws, row, c0, c1, text, color=REDT, bold=True, size=8.5):
    c = span(ws, row, c0, c1)
    c.value = text
    c.font = f(size, bold, color)
    c.alignment = WRP   # wrapped, so long notes cannot bleed past the last column
    ws.row_dimensions[row].height = 16


def dv(ws, options, ranges):
    v = DataValidation(type="list", formula1='"%s"' % ",".join(options),
                       allow_blank=True, showDropDown=False)
    v.errorTitle, v.error = "Not on the list", "Pick one from the drop-down."
    ws.add_data_validation(v)
    for rng in ranges:
        v.add(rng)


def gold_when_short(ws, rng):
    ws.conditional_formatting.add(rng, CellIsRule(
        operator="greaterThan", formula=["0"],
        fill=PatternFill("solid", fgColor=GOLD),
        font=Font(name=FONT, size=9.5, bold=True, color=REDT)))


def red_when(ws, rng, values):
    for val in values:
        ws.conditional_formatting.add(rng, CellIsRule(
            operator="equal", formula=['"%s"' % val],
            fill=PatternFill("solid", fgColor=REDF),
            font=Font(name=FONT, size=9.5, bold=True, color=REDT)))


# ================================================================== build ===
wb = Workbook()


def new_side(name):
    """A sheet set up to print as exactly one page: fit-to-width, one page tall."""
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    for col, w in WIDTHS.items():
        ws.column_dimensions[L(col)].width = w
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.orientation = "portrait"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = ws.page_margins.right = 0.3
    ws.page_margins.top = ws.page_margins.bottom = 0.35
    ws.page_margins.header = ws.page_margins.footer = 0.15
    ws.oddFooter.center.text = "One sheet, printed double-sided (flip on long edge)  -  &A"
    ws.oddFooter.center.size = 7
    ws.oddFooter.center.font = "Arial,Italic"
    return ws


wb.remove(wb.active)
ws = new_side("SIDE 1 - FRONT")

# ------------------------------------------------------- SIDE 1 (front) -----
title(ws, 1, "TOWNHALL   |   BAR TASTE PLATE   -   SPRING / SUMMER 2026")
subtitle(ws, 2, "SIDE 1 of 2      COUNT & ORDER      Batches + Mixers  /  Fresh + Garnish")

# date / shift / name
ws.row_dimensions[3].height = 21
for lbl_c, val_c0, val_c1, text in [(1, 2, 3, "DATE"), (4, 5, 6, "SHIFT"),
                                    (7, 8, 11, "COMPLETED BY")]:
    lb = ws.cell(row=3, column=lbl_c, value=text)
    lb.font = f(8.5, True, NAVY)
    lb.alignment = Alignment(horizontal="right", vertical="center")
    cell = span(ws, 3, val_c0, val_c1)
    cell.fill = INPUT
    cell.font = f(10, True)
    cell.alignment = CTR
    for col in range(val_c0, val_c1 + 1):
        ws.cell(row=3, column=col).border = Border(bottom=Side(style="medium", color=NAVY))

for lrow, ltext in [
        (4, "Fill in the YELLOW boxes only.   NEED = PAR minus ON HAND, e.g. PAR 8 + ON HAND 5 "
            "= NEED 3.   Gold means make or order more."),
        (5, "STATUS:   OK = good to go   /   LOW = running out, tell prep   /   86 = out, tell a "
            "manager + post in GroupMe")]:
    c = span(ws, lrow, 1, LAST_C)
    c.value = ltext
    c.font = f(8, False, "404040")
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
    ws.row_dimensions[lrow].height = 14
ws.row_dimensions[6].height = 6

HDR = 7
col_header(ws, HDR, LEFT_C, ["ITEM", "PAR", "ON\nHAND", "NEED", "STATUS"])
col_header(ws, HDR, RIGHT_C, ["ITEM", "PAR", "ON\nHAND", "NEED", "STATUS"])

# left: batches then mixers
r = HDR + 1
band(ws, r, LEFT_C, LEFT_C + 4, "COCKTAIL BATCHES")
r += 1
lb_start = r
for name, par, unit in BATCHES:
    count_row(ws, r, LEFT_C, name, par, unit)
    r += 1
band(ws, r, LEFT_C, LEFT_C + 4, "JUICES & MIXERS")
r += 1
for name, par, unit in MIXERS:
    count_row(ws, r, LEFT_C, name, par, unit)
    r += 1
lb_end = r - 1
left_bottom = r

# right: fresh counted then garnish status
r = HDR + 1
band(ws, r, RIGHT_C, RIGHT_C + 4, "FRESH - COUNT IN SIXTH PANS")
r += 1
rb_start = r
for name, par, unit in FRESH_COUNT:
    count_row(ws, r, RIGHT_C, name, par, unit)
    r += 1
fresh_count_end = r - 1
band(ws, r, RIGHT_C, RIGHT_C + 4, "GARNISH & DRY GOODS")
r += 1
for name in FRESH_YN:
    status_row(ws, r, RIGHT_C, name)
    r += 1
rb_end = r - 1
right_bottom = r

side1_bottom = max(left_bottom, right_bottom)
note(ws, side1_bottom, LEFT_C, LEFT_C + 4, BATCH_NOTE)
note(ws, side1_bottom, RIGHT_C, RIGHT_C + 4,
     "Anything LOW or 86 -> tell prep + a manager.", color=REDT)
side1_bottom += 1
turn = span(ws, side1_bottom, 1, LAST_C)
turn.value = "TURN OVER  ->  SIDE 2:  BAR TOOLS, SET-UP & DAILY COMMUNICATION"
turn.font = f(9, True, NAVY)
turn.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
turn.fill = PatternFill("solid", fgColor=GREY)
for col in range(1, LAST_C + 1):
    ws.cell(row=side1_bottom, column=col).fill = PatternFill("solid", fgColor=GREY)
ws.row_dimensions[side1_bottom].height = 18

# validation + highlighting, side 1
left_status = f"{L(LEFT_C+4)}{lb_start}:{L(LEFT_C+4)}{lb_end}"
right_status = f"{L(RIGHT_C+4)}{rb_start}:{L(RIGHT_C+4)}{rb_end}"
dv(ws, ["OK", "LOW", "86"], [left_status, right_status])
gold_when_short(ws, f"{L(LEFT_C+3)}{lb_start}:{L(LEFT_C+3)}{lb_end}")
gold_when_short(ws, f"{L(RIGHT_C+3)}{rb_start}:{L(RIGHT_C+3)}{fresh_count_end}")
red_when(ws, left_status, ["86"])
red_when(ws, right_status, ["86"])
ws.cell(row=lb_start, column=LEFT_C + 1).comment = Comment(
    "PARs carried over from the original Spring/Summer 2026 taste plate. "
    "Change a PAR and NEED updates itself.", "TownHall")

ws.print_area = f"A1:{L(LAST_C)}{side1_bottom}"
ws.freeze_panes = "A8"

# -------------------------------------------------------- SIDE 2 (back) -----
ws = new_side("SIDE 2 - BACK")

title(ws, 1, "TOWNHALL   |   BAR TASTE PLATE   -   SPRING / SUMMER 2026")
subtitle(ws, 2, "SIDE 2 of 2      BAR TOOLS, SET-UP & DAILY COMMUNICATION")
# same sheet of paper as side 1, so the date and name carry over
ws.row_dimensions[3].height = 16
c = span(ws, 3, 1, LAST_C)
c.value = ("=\"Date: \"&IF('SIDE 1 - FRONT'!B3=\"\",\"__________\",'SIDE 1 - FRONT'!B3)"
           "&\"     Shift: \"&IF('SIDE 1 - FRONT'!E3=\"\",\"______\",'SIDE 1 - FRONT'!E3)"
           "&\"     Completed by: \"&IF('SIDE 1 - FRONT'!H3=\"\",\"__________________\","
           "'SIDE 1 - FRONT'!H3)")
c.font = f(8.5, True, "404040")
c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
ws.row_dimensions[4].height = 5
r = 5
side2_top = r

# --- left: bar tools
band(ws, r, LEFT_C, LEFT_C + 4, "BAR TOOL COUNT")
r += 1
col_header(ws, r, LEFT_C, ["TOOL", "PAR", "ON\nHAND", "NEED", "COND."])
r += 1
tool_start = r
for name in TOOLS:
    it = ws.cell(row=r, column=LEFT_C, value=name)
    it.font = f(9.5)
    it.alignment = LFT
    par = ws.cell(row=r, column=LEFT_C + 1)
    par.fill = INPUT
    par.font = f(9.5, True, "0000FF")
    par.alignment = CTR
    have = ws.cell(row=r, column=LEFT_C + 2)
    have.fill = INPUT
    have.font = f(9.5, True)
    have.alignment = CTR
    pl, hl = L(LEFT_C + 1), L(LEFT_C + 2)
    need = ws.cell(row=r, column=LEFT_C + 3,
                   value=f'=IF(OR({pl}{r}="",{hl}{r}=""),"",MAX(0,{pl}{r}-{hl}{r}))')
    need.font = f(9.5, True)
    need.alignment = CTR
    cond = ws.cell(row=r, column=LEFT_C + 4)
    cond.fill = INPUT
    cond.font = f(9.5)
    cond.alignment = CTR
    for col in range(LEFT_C, LEFT_C + 5):
        ws.cell(row=r, column=col).border = BOX
    ws.row_dimensions[r].height = 22
    r += 1
tool_end = r - 1

tl = span(ws, r, LEFT_C, LEFT_C + 2)
tl.value = "TOOLS SHORT TODAY"
tl.font = f(9.5, True, NAVY)
tl.alignment = Alignment(horizontal="right", vertical="center")
tot = ws.cell(row=r, column=LEFT_C + 3,
              value=f"=SUM({L(LEFT_C+3)}{tool_start}:{L(LEFT_C+3)}{tool_end})")
tot.font = f(10, True, REDT)
tot.alignment = CTR
tot.border = BOX
ws.cell(row=r, column=LEFT_C + 4).border = BOX
ws.row_dimensions[r].height = 20
r += 1
note(ws, r, LEFT_C, LEFT_C + 4,
     "PAR is blank on purpose - set it once with your bar lead.")
ws.row_dimensions[r].height = 16
r += 1

# --- left: set-up walk
band(ws, r, LEFT_C, LEFT_C + 4, "BAR SET-UP WALK")
r += 1
col_header(ws, r, LEFT_C, ["ITEM", "WHAT TO CHECK", "", "", "DONE"])
ws.merge_cells(start_row=r, start_column=LEFT_C + 1, end_row=r, end_column=LEFT_C + 3)
r += 1
setup_start = r
for name, action in SETUP:
    it = ws.cell(row=r, column=LEFT_C, value=name)
    it.font = f(9.5)
    it.alignment = LFT
    act = span(ws, r, LEFT_C + 1, LEFT_C + 3)
    act.value = action
    act.font = f(8.5, color="404040")
    act.alignment = LFT
    done = ws.cell(row=r, column=LEFT_C + 4)
    done.fill = INPUT
    done.font = f(9.5, True)
    done.alignment = CTR
    for col in range(LEFT_C, LEFT_C + 5):
        ws.cell(row=r, column=col).border = BOX
    ws.row_dimensions[r].height = 20
    r += 1
setup_end = r - 1
left2_bottom = r

# --- right: daily communication
r = side2_top
band(ws, r, RIGHT_C, RIGHT_C + 4, "DAILY COMMUNICATION")
r += 1
comm_rows = []
for question, options, flag in COMMS:
    q = span(ws, r, RIGHT_C, RIGHT_C + 3)
    q.value = question
    q.font = f(9.5, True)
    q.alignment = WRP
    a = ws.cell(row=r, column=RIGHT_C + 4)
    a.fill = INPUT
    a.font = f(9.5, True)
    a.alignment = CTR
    for col in range(RIGHT_C, RIGHT_C + 5):
        ws.cell(row=r, column=col).border = BOX
    ws.row_dimensions[r].height = 24
    dv(ws, options, [f"{L(RIGHT_C+4)}{r}"])
    comm_rows.append((r, flag))
    r += 1
r += 1

band(ws, r, RIGHT_C, RIGHT_C + 4, "86'd ITEMS  +  NOTES FOR THE NEXT SHIFT")
r += 1
for _ in range(11):
    line = span(ws, r, RIGHT_C, RIGHT_C + 4)
    line.fill = INPUT
    line.alignment = LFT
    line.font = f(9.5)
    for col in range(RIGHT_C, RIGHT_C + 5):
        ws.cell(row=r, column=col).border = BOX
    ws.row_dimensions[r].height = 21
    r += 1
r += 1

band(ws, r, RIGHT_C, RIGHT_C + 4, "SIGN OFF")
r += 1
for label in ("Bartender / barback", "Time finished", "Manager verified"):
    lb = span(ws, r, RIGHT_C, RIGHT_C + 2)
    lb.value = label
    lb.font = f(9.5, True)
    lb.alignment = LFT
    sig = span(ws, r, RIGHT_C + 3, RIGHT_C + 4)
    sig.fill = INPUT
    for col in range(RIGHT_C, RIGHT_C + 5):
        ws.cell(row=r, column=col).border = BOX
    ws.row_dimensions[r].height = 24
    r += 1
right2_bottom = r

bottom = max(left2_bottom, right2_bottom)
note(ws, bottom, 1, LAST_C,
     "EVERY 86'd ITEM:  tell a manager AND post it in GroupMe before you leave the bar.")
ws.row_dimensions[bottom].height = 18

# validation + highlighting, side 2
dv(ws, ["OK", "DIRTY", "BROKEN", "MISSING"],
   [f"{L(LEFT_C+4)}{tool_start}:{L(LEFT_C+4)}{tool_end}"])
dv(ws, ["YES", "NO"], [f"{L(LEFT_C+4)}{setup_start}:{L(LEFT_C+4)}{setup_end}"])
gold_when_short(ws, f"{L(LEFT_C+3)}{tool_start}:{L(LEFT_C+3)}{tool_end}")
red_when(ws, f"{L(LEFT_C+4)}{tool_start}:{L(LEFT_C+4)}{tool_end}", ["BROKEN", "MISSING"])
red_when(ws, f"{L(LEFT_C+4)}{setup_start}:{L(LEFT_C+4)}{setup_end}", ["NO"])
for row, flag in comm_rows:
    cell_rng = f"{L(RIGHT_C+4)}{row}"
    if flag == "NO":
        red_when(ws, cell_rng, ["NO"])
    else:
        ws.conditional_formatting.add(cell_rng, CellIsRule(
            operator="equal", formula=['"YES"'],
            fill=PatternFill("solid", fgColor=GOLD),
            font=Font(name=FONT, size=9.5, bold=True, color=REDT)))
ws.cell(row=tool_start, column=LEFT_C + 1).comment = Comment(
    "Bar tool PARs were not on the original sheet. Set them once (per well plus "
    "back-ups) and NEED takes care of the rest.", "TownHall")

ws.print_area = f"A1:{L(LAST_C)}{bottom}"

wb.save(OUT)
print("wrote", OUT, "| side 1 rows 1-%d | side 2 rows 1-%d" % (side1_bottom, bottom))
