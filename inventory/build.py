import json, glob, re, html, datetime, os
S = "/tmp/claude-0/-home-user-townhall-ordering/c4d4c947-be19-52f0-a291-3618ed25ca3e/scratchpad"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lbw-inventory-sheet.html")

def esc(s): return html.escape(str(s))

SIZE = re.compile(r"(\d+(?:\.\d+)?)\s*(ml|milliliters|l|liter|oz|fluid ounces)\b", re.I)
def clean_unit(u):
    u = (u or "").strip()
    if not u or u in ("Other", "Each", "Case", "Gallon"):
        return u
    keg = re.search(r"1/(2|4|6)\s*BBL|50L", u)
    if u.lower().startswith("keg"):
        return {"2": "1/2 bbl keg", "4": "1/4 bbl keg", "6": "1/6 bbl keg"}.get(keg.group(1), "Keg") if keg and keg.group(0) != "50L" else ("50L keg" if keg else "Keg")
    container = next((c for c in ("Bottle", "Can") if c.lower() in u.lower()), "")
    if "(Liter)" in u:
        return f"{container or 'Bottle'} · 1L"
    m = SIZE.search(u)
    if not m:
        return container or u
    n, unit = m.group(1), m.group(2).lower()
    unit = {"milliliters": "mL", "ml": "mL", "l": "L", "liter": "L", "fluid ounces": "oz", "oz": "oz"}[unit]
    return f"{container} · {n}{unit}" if container else f"{n}{unit}"

products = {p["companyConceptProductId"]: p for p in json.load(open(f"{S}/products.json"))}
lines = []
ids = set(l.strip() for f in glob.glob(f"{S}/chunk_0*") for l in open(f) if l.strip())
for f in sorted(glob.glob(f"{S}/raw/*.json")):
    o = json.load(open(f))
    if o["orderId"] not in ids or o.get("isCredit"):
        continue
    for li in o.get("lineItems") or []:
        lines.append(dict(li, orderId=o["orderId"], createdDate=o["createdDate"], vendorName=o["vendorName"]))

CATS = {"14167": "Liquor", "13376": "Wine", "1488": "Beer · Bottle & Can", "1489": "Beer · Draft"}
CAT_ORDER = ["Liquor", "Wine", "Beer · Bottle & Can", "Beer · Draft"]
VENDOR_SHORT = {
    "Southern Glazer's Of OH": "Southern Glazer's",
    "The Columbus Distributing Co": "Columbus Distributing",
    "Heidelberg Distributing Co": "Heidelberg Distributing",
}

items = {}  # (vendor, productId) -> info
for l in lines:
    pid = str(l.get("companyConceptProductId") or "")
    p = products.get(pid)
    if not p:
        continue
    cat = None
    for c in sorted(p["categories"], key=lambda c: -c["percentAllocation"]):
        if c["categoryId"] in CATS:
            cat = CATS[c["categoryId"]]; break
    if not cat or re.search(r"deposit|return", p["productName"], re.I):
        continue  # deposits, mixers, freight, supplies
    key = (l["vendorName"], pid)
    it = items.setdefault(key, {
        "name": p["productName"].strip(), "unit": clean_unit(p.get("reportByUnit")),
        "cat": cat, "codes": set(), "last": "", "cost": None,
    })
    if l.get("vendorItemCode"):
        it["codes"].add(str(l["vendorItemCode"]).strip())
    if l.get("unitPrice") and l["createdDate"] >= it["last"]:
        it["last"] = l["createdDate"]
        it["cost"] = l["unitPrice"]

vendors = {}
for (v, pid), it in items.items():
    vendors.setdefault(v, []).append(it)

def short_date(d):
    return datetime.date.fromisoformat(d).strftime("%-m/%-d") if d else ""

total = sum(len(v) for v in vendors.values())
sections = []
for v in sorted(vendors, key=lambda v: VENDOR_SHORT.get(v, v).lower()):
    its = vendors[v]
    rows = []
    for cat in CAT_ORDER:
        group = sorted([i for i in its if i["cat"] == cat], key=lambda i: i["name"].lower())
        if not group:
            continue
        rows.append(f'<tr class="cat"><th colspan="6">{esc(cat)} <span>{len(group)}</span></th></tr>')
        for i in group:
            code = ", ".join(sorted(i["codes"]))[:24]
            cost = f'${i["cost"]:,.2f}' if isinstance(i["cost"], (int, float)) else ""
            rows.append(
                f'<tr><td class="name">{esc(i["name"])}</td><td class="code">{esc(code)}</td>'
                f'<td class="unit">{esc(i["unit"])}</td><td class="num">{cost}</td>'
                f'<td class="write"></td><td class="write"></td></tr>')
    sections.append(f'''
<section class="vendor{" small" if len(its) <= 30 else ""}">
  <header class="vhead"><h2>{esc(VENDOR_SHORT.get(v, v))}</h2><p>{len(its)} products</p></header>
  <div class="tablewrap"><table>
    <colgroup><col class="c-name"><col class="c-code"><col class="c-unit"><col class="c-cost"><col class="c-w"><col class="c-w"></colgroup>
    <thead><tr><th>Product</th><th>Item #</th><th>Count unit</th><th class="num">Last cost</th><th>On hand</th><th>Order</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table></div>
</section>''')

vendor_index = "".join(
    f'<li><span>{esc(VENDOR_SHORT.get(v, v))}</span><b>{len(vendors[v])}</b></li>'
    for v in sorted(vendors, key=lambda v: VENDOR_SHORT.get(v, v).lower()))

dates = sorted(l["createdDate"] for l in lines)
tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")).read()
out = (tpl.replace("{{SECTIONS}}", "".join(sections))
          .replace("{{INDEX}}", vendor_index)
          .replace("{{TOTAL}}", str(total))
          .replace("{{NVENDORS}}", str(len(vendors)))
          .replace("{{RANGE}}", f'{datetime.date.fromisoformat(dates[0]).strftime("%b %-d")} – {datetime.date.fromisoformat(dates[-1]).strftime("%b %-d, %Y")}'))
import os; os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(out)
print(total, "products,", len(vendors), "vendors")
for v in sorted(vendors): print(f"  {v}: {len(vendors[v])}")
