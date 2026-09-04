import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import column_index_from_string

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Game Day Pre-Shift"

F = lambda s=12, b=False, i=False, c="000000": Font(name="Calibri", size=s, bold=b, italic=i, color=c)
B12, R12, B14, B11, R11 = F(12, True), F(12), F(14, True), F(11, True), F(11)
BI11 = F(11, True, True)
I10 = F(10, False, True, "595959")

med, thin = Side(style="medium"), Side(style="thin")
BOX = Border(top=med, bottom=med, left=med, right=med)
THINBOX = Border(top=thin, bottom=thin, left=thin, right=thin)
UNDER = Border(bottom=thin)
GREY = PatternFill("solid", fgColor="EDEDED")
DARK = PatternFill("solid", fgColor="D9D9D9")

CEN = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
TOPL = Alignment(horizontal="left", vertical="top", wrap_text=True)

for col, w in {"A": 16.5, "B": 11, "C": 15, "D": 20, "E": 17, "F": 11, "G": 11}.items():
    ws.column_dimensions[col].width = w

def band(row, c1, c2, value, font=B12, align=LEFT, border=None, fill=None, height=None):
    ws.merge_cells(start_row=row, end_row=row, start_column=c1, end_column=c2)
    cell = ws.cell(row=row, column=c1)
    cell.value, cell.font, cell.alignment = value, font, align
    if border or fill:
        for cc in range(c1, c2 + 1):
            t = ws.cell(row=row, column=cc)
            if border: t.border = border
            if fill: t.fill = fill
    if height: ws.row_dimensions[row].height = height

def box(row1, row2, c1, c2, height=18):
    ws.merge_cells(start_row=row1, end_row=row2, start_column=c1, end_column=c2)
    ws.cell(row=row1, column=c1).alignment = TOPL
    for r in range(row1, row2 + 1):
        ws.row_dimensions[r].height = height
        for cc in range(c1, c2 + 1):
            ws.cell(row=r, column=cc).border = THINBOX

def lab(row, col, text, font=B12):
    c = ws.cell(row=row, column=col)
    c.value, c.font, c.alignment = text, font, LEFT

def rule(row, c1, c2):
    for c in range(c1, c2 + 1):
        ws.cell(row=row, column=c).border = UNDER

def checks(row, items):
    for item in items:
        c = ws.cell(row=row, column=1)
        c.value, c.font, c.alignment = "☐", F(14), CEN
        band(row, 2, 7, item, R11, LEFT, height=17)
        row += 1
    return row

r = 1
band(r, 1, 7, "TOWNHALL CLE  —  GAME DAY PRE-SHIFT", B14, CEN, fill=DARK, height=24); r += 1
band(r, 1, 7, "Read this at pre-shift. Do not summarize it.", I10, CEN); r += 2

for left, right in [("DATE:", "MATCHUP:"), ("DAY:", "KICKOFF:"),
                    ("SHIFT:  AM / PM", "DOORS:"), ("MANAGER ON DUTY:", "EXPECTED VOLUME:")]:
    lab(r, 1, left);  rule(r, 2, 3)
    lab(r, 4, right); rule(r, 6, 7)
    r += 1
r += 1

band(r, 1, 7, "THE THREE WINDOWS — WRITE THE TIMES ON THE BOARD", B12, LEFT, fill=GREY, height=18); r += 1
for name, note in [
    ("PRE-GAME", "Volume and speed, turn-and-burn. Guests have a hard out."),
    ("GAME WINDOW", "Floor thins, bar fills. It feels slow. It is not — it is the setup."),
    ("POST-GAME", "Hardest 90 minutes of the week. All hands on the floor before the final whistle."),
]:
    lab(r, 1, name, B11); rule(r, 2, 2)
    band(r, 3, 7, note, R11, LEFT, height=16); r += 1
r += 1

band(r, 1, 7, "THE THREE HARD LINES — SAY ALL THREE OUT LOUD, EVERY GAME DAY", B12, CEN, border=BOX, fill=DARK, height=20); r += 1
for i, line in enumerate([
    '1.  NO DRINKING — not before your shift, not on your shift, not on the clock in any capacity. Not a taste, not a guest-bought round, not overtime.',
    '2.  NO PROMO BOTTLES — no bottle leaves the bar as a promo, comp, gift or bucket. Every bottle rings in and gets paid for. Every single one.',
    '3.  NO DISCOUNTS — every check rings at full price. No employee rate for a friend, no "take care of them." You do not have discount authority.',
    "NOTE: a promo bottle is NOT bottle service. Bottle service is a product we SELL and ring at full price — sell it hard. A promo bottle is one that leaves with no ticket. Sell every bottle. Give away none.",
    "If a guest needs to be taken care of, GET A MANAGER. You will never get in trouble for getting a manager. You will get in trouble for making the call yourself.",
]):
    band(r, 1, 7, line, B11 if i < 3 else BI11, LEFT, border=BOX, height=30); r += 1  # 4th+ lines italic
r += 1

band(r, 1, 7, "ID'ING — NO EXCEPTIONS, NOT ON GAME DAY", B12, CEN, border=BOX, fill=DARK, height=20); r += 1
for line in [
    "Every guest who looks under 40 gets carded. Every time. At the bar, at the table, and again if someone hands them a drink they did not order.",
    "Physical ID only. Expired is not an ID. A vertical license means look twice and do the math out loud.",
    "If you are not sure, you do not pour. Hand it to a manager — that is the whole process, and nobody gets second-guessed for using it.",
    "Game day is the night we get tested on this. The liquor license is the entire business. One bad pour costs more than the whole night made.",
]:
    band(r, 1, 7, line, R11, LEFT, border=BOX, height=28); r += 1
r += 1

lab(r, 1, "GOAL / CONTEST FOR THE DAY:"); r += 1
box(r, r + 1, 1, 7, 20); r += 3

lab(r, 1, "NEW BEERS / NEW ITEMS:"); r += 1
box(r, r + 1, 1, 7); r += 3

lab(r, 1, "86:"); r += 1
box(r, r + 1, 1, 7); r += 3

band(r, 1, 7, "PROMOS FOR THE DAY — EVERYBODY KNOWS ALL THREE BEFORE DOORS", B12, LEFT, fill=GREY, height=18); r += 1
for name, price, note in [
    ("Suncruiser Buckets", "6 / 30", "Lead with this at every table in the pre-game window. Fastest ticket in the building."),
    ("Lucky One Lemonade", "6 / 24", "Same play. Buckets land on the table before the first food order goes in."),
    ("Tito's Bottle Service", "PUSH HARD", "The one we are chasing tonight. Offer it to every large party, every booth, every group already celebrating. Rings at full price — bottle service is sold, never comped."),
]:
    lab(r, 1, name, B11)
    lab(r, 3, price, F(11, True, False, "A4211B" if price == "PUSH HARD" else "2C574A"))
    band(r, 4, 7, note, R11, LEFT, height=30)
    r += 1
lab(r, 1, "Other promos:", R11); rule(r, 2, 7); ws.row_dimensions[r].height = 18
r += 2

# ---- staff grid ----
head = r
lab(head, 1, "STAFF #'S"); lab(head, 3, "SHIFT LEADS:"); lab(head, 5, "STAFF TO COACH:")
r += 1
staff = ["SERVERS:", "BARTENDERS:", "CAFÉ:", "HOSTS:", "RUNNERS:", "BARBACKS:", "SHOT GIRL:", "MANAGERS:"]
leads = ["SERVER:", "CAFÉ:", "BARTENDER:", "HOST:", "BAR:", "BARBACK:"]
for i, s in enumerate(staff):
    lab(r + i, 1, s, R12); rule(r + i, 2, 2)
    ws.row_dimensions[r + i].height = 19
for i, s in enumerate(leads):
    lab(r + i, 3, s, R12); rule(r + i, 4, 4)

lab(r, 5, "1 HUDDL COMPLETION")
for i, s in enumerate(["SERVER:", "BAR:", "CAFÉ:", "HOST:", "BARBACK:"]):
    lab(r + 1 + i, 5, s, R12); rule(r + 1 + i, 6, 6)
r = max(r + len(staff), r + len(leads), r + 6) + 1

lab(r, 5, "7SHIFTS COMPLETION")
for i, s in enumerate(["SERVER:", "BAR:", "CAFÉ:", "HOST:", "BARBACK:"]):
    lab(r + 1 + i, 5, s, R12); rule(r + 1 + i, 6, 6)

lab(r, 1, "CLEANING DUTIES:")
box(r + 1, r + 2, 1, 4)
r += 7   # clear the 7shifts column on the right before starting a full-width block

band(r, 1, 7, "STATION ASSIGNMENTS — WRITE A NAME ON EVERY LINE", B12, LEFT, fill=GREY, height=18); r += 1

def group(top, col, title, slots):
    """One position group: bold title, then a named line per station."""
    lab(top, col, title, B11)
    for i, s in enumerate(slots):
        lab(top + 1 + i, col, s, R11)
        end = 7 if col == 5 else col + 1
        rule(top + 1 + i, col + 1, end)
        ws.row_dimensions[top + 1 + i].height = 18
    return top + 1 + len(slots)

band1 = r
e1 = group(band1, 1, "HOST", ["Lead:", "Runner:", "Waters:", "Bathrooms:"])
e2 = group(band1, 3, "RUNNERS", ["Bar 100:", "Bar 200:", "Food:"])
e3 = group(band1, 5, "BAR", ["100:", "105:", "110:", "200:", "Patio:"])
r = max(e1, e2, e3) + 1

band2 = r
e4 = group(band2, 1, "BARBACKS", ["Main Bar:", "Patio Bar:", "Main Floor:", "Café:", "Front Patio:"])
e5 = group(band2, 3, "SHOT GIRL", ["On tonight:"])
e6 = group(band2, 5, "TASTE PLATE", ["Running it:"])
r = max(e4, e5, e6) + 1

lab(r, 1, "PARTIES / EVENTS:"); r += 1
box(r, r + 1, 1, 7); r += 3

band(r, 1, 7, "GAME DAY OPEN — 90 MINUTES BEFORE DOORS", B12, LEFT, fill=GREY, height=18); r += 1
r = checks(r, [
    "Know the game — kickoff, attendance, national TV, weather. Times on the board.",
    "Every staff member can name all three promos — ask two people at random before pre-shift ends.",
    "Three windows built on paper — cut times, breaks, post-game all-hands decided now.",
    "Staffing confirmed against 7shifts. One no-show on game day is a two-hour wait.",
    "Every station walked, front and back. The 3 Rules on all of them.",
    "Bar par DOUBLED — ice, kegs, backups, garnish, glassware, batch.",
    "86 board walked with the kitchen, current and visible.",
    "Mains timing called out — nothing fires before 5:00 PM.",
    "TVs, sound and the game feed tested before a single guest sits down.",
    "ID check covered — door and bar know who is carding, and the light works.",
    "Restrooms stocked, and a name on the 45-minute rotation.",
    "POS, printers and card processing tested with a live ticket.",
    "Cash on hand for a bar that will run cash all night.",
    "Door, patio and line plan — where the wait forms and who holds it.",
])
r += 1

for l, rt in [("IS STAFF IN UNIFORM?   YES / NO", "SERVERS HAVE WINE KEY & LIGHTER?   YES / NO"),
              ("ID'ING EVERYONE UNDER 40?   YES / NO", "TVs & GAME FEED TESTED?   YES / NO")]:
    band(r, 1, 3, l, B12, CEN, border=BOX, height=20)
    band(r, 4, 7, rt, B12, CEN, border=BOX)
    r += 1
band(r, 1, 7, "**REMIND STAFF TO TEXT FRIENDS TO COME VISIT**", B12, CEN, border=BOX, height=20); r += 2

band(r, 1, 7, "BY POSITION — READ THE BLOCK THAT BELONGS TO EACH GROUP", B12, LEFT, fill=GREY, height=18); r += 1
for name, note in [
    ("BAR", "ID before you pour — every time, no exceptions. Every drink rings before it pours. No promo bottles, no comps. Cut people early and tell a manager immediately. Stock backups during the game window, not after it."),
    ("SERVERS", 'Greet inside 30 seconds. Ask "are you trying to be out by kickoff?" first, then fire accordingly. Card every table before the first round lands. Full hands in, full hands out. Guest issue goes to a manager immediately.'),
    ("HOST", "Own the door and own the wait. An accurate quote beats a short one — give a real number, then beat it. Card at the door when the room is young; it is far easier there than at the bar. Keep the line off the sidewalk and feed the wait to the bar."),
    ("KITCHEN", "Prep to game-day pars, confirmed before service. 86 goes to the manager when you see it coming, not when you hit zero. Ticket times called every window. Original position, original condition at every changeover."),
    ("SUPPORT", "You set the pace of the building. Restrooms, trash, glassware and ice on a rotation, not on request. Everybody runs food."),
]:
    lab(r, 1, name, B11)
    band(r, 2, 7, note, R11, LEFT, height=32); r += 1
r += 1

band(r, 1, 7, "POST-GAME & CLOSE", B12, LEFT, fill=GREY, height=18); r += 1
r = checks(r, [
    "All hands on the floor BEFORE the final whistle — not after.",
    "Full bottle count and bar inventory tonight, not tomorrow.",
    "Every void, comp and discount reconciled to a manager name.",
    "Every refusal or cut-off logged with what happened and who made the call.",
    "Every station back to original position, original condition.",
    "Shift notes written: what we ran out of, where the wait broke down, what changes next game.",
])
r += 1

lab(r, 1, "MARKETING:"); r += 1
box(r, r + 1, 1, 7); r += 3

lab(r, 1, "OTHER IMPORTANT NOTES:"); r += 1
box(r, r + 2, 1, 7); r += 4

band(r, 1, 7, "100% of our standards, 100% of the time, at 100% volume. A full house is not an excuse to run at 80% — it is the reason we hold the line.",
     BI11, CEN, height=28)

ws.page_setup.orientation = "portrait"
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 0
ws.sheet_properties.pageSetUpPr.fitToPage = True
for m in ("left", "right", "top", "bottom"):
    setattr(ws.page_margins, m, 0.4)
ws.print_area = f"A1:G{r}"

out = "/home/user/townhall-ordering/docs/GameDay_PreShift_Template.xlsx"
wb.save(out)
print("saved", out, "last row", r)
