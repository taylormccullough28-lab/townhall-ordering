#!/usr/bin/env python3
"""Generate the bartender certification sheet for each TownHall location.

One spec table drives both editions so the test can never drift from the
build sheets: glassware is parameterised, and Espresso Martini is
Short North only.
"""
import io, html

# ---------------------------------------------------------------- spec data
# rocks_glass / rocks_ice are substituted per location.
DRINKS = [
    dict(name="Channel Orange", glass="{rocks}", ice="{ice}",
         garnish="Sage + cinnamon stick", total="4.25 oz",
         pours=[("2.00", "Channel Orange Biz"), ("1.75", "Pear Chai Biz"),
                ("0.50", "Lemon juice")]),
    dict(name="Don't Worry About It Sweetheart", glass="{rocks}", ice="{ice}",
         garnish="Rosemary sprig", total="6.00 oz",
         pours=[("2.00", "DWAIS Biz"), ("3.50", "Cider Mix Biz"),
                ("0.50", "Lemon juice")]),
    dict(name="Green Goddess", glass="{rocks} — Pernod-rinsed", ice="{ice}",
         garnish="Mint bushel", total="4.25 oz",
         pours=[("rinse", "Pernod — in the glass, not the tin"),
                ("2.75", "Goddess Biz"), ("0.50", "Spicy cucumber juice"),
                ("1.00", "Lemon juice")]),
    dict(name="LMF 2.0", glass="{rocks}", ice="{ice}",
         garnish="Dragonfruit powder dusting, then a pinch of calendula",
         total="4.75 oz",
         pours=[("4.00", "LMF 2.0 Biz"), ("0.25", "Turmeric juice"),
                ("0.50", "Lemon juice")]),
    dict(name="No New Friends", glass="12 oz tall", ice="Fresh ice",
         garnish="Hibiscus leaves + tarragon sprig", total="4.00 oz + soda",
         pours=[("3.00", "NNF Biz"), ("1.00", "Lime juice"),
                ("top", "Soda water — after the shake")]),
    dict(name="Chai Hard", glass="Coupe / martini", ice="None — served up",
         garnish="1 star anise", total="4.75 oz",
         pours=[("2.25", "Titos Chai Biz"), ("1.00", "Blonde espresso"),
                ("1.50", "Pecan brown sugar syrup"), ("pinch", "Himalayan salt")]),
    dict(name="Espresso Martini", glass="Martini coupe", ice="None — served up",
         garnish="3 espresso beans", total="5.00 oz", short_north_only=True,
         pours=[("2.00", "Liquor of choice — ask the guest"),
                ("1.00", "Simple syrup"), ("2.00", "Espresso")]),
    dict(name="Scarlett Spritz", glass="Wine", ice="Packed",
         garnish="Rosemary", total="7.50 oz",
         pours=[("2.50", "Spritz Biz — in first, under the Prosecco"),
                ("5.00", "Prosecco")]),
]

QUESTIONS = [
    ("Which drink on this menu is never shaken, and what happens if you shake it?",
     "Scarlett Spritz. It is built in the glass. Shaking flattens the Prosecco."),
    ("Where does the Pernod go on a Green Goddess, and at what point in the build?",
     "In the glass, not the tin. Rinse and dump the excess before you shake."),
    ("When is the soda added to a No New Friends, and why never in the tin?",
     "After the shake, in the glass. Shaking soda kills the bubbles and can "
     "blow the tin apart."),
    ("{updrinks_q}", "{updrinks_a}"),
    ("In what order do the two LMF 2.0 garnishes go on, and why does it matter?",
     "Dragonfruit powder first, then the calendula. Dusting over the flowers "
     "buries them."),
    ("Why do you strain over fresh ice instead of the ice you shook with?",
     "Shaken ice is chipped and already melting; it waters the drink down in "
     "the glass."),
    ("Which drink has no fixed total pour, and why?",
     "No New Friends. The soda tops the glass rather than being measured."),
    ("A guest orders a drink and you are out of the biz. What do you do?",
     "Tell the guest it is unavailable and call it to the bar lead. Never "
     "substitute or free-pour a replacement."),
]

EM_QUESTION = ("What must you do before you start building an Espresso Martini?",
               "Ask the guest which liquor they want. It is the only spec with "
               "no liquor written into it.")

LOCATIONS = {
    "short-north": dict(
        label="TownHall Short North", title="Short North Certification", key_title="Short North Answer Key",
        rocks="Rocks", ice="Fresh rocks ice", espresso_martini=True,
        updrinks_q="Which two drinks are served up, and what does that mean for the glass?",
        updrinks_a="Chai Hard and Espresso Martini. Chilled coupe, no ice in the glass."),
    "ohio-city": dict(
        label="TownHall Ohio City", title="Ohio City Certification", key_title="Ohio City Answer Key",
        rocks="Emulsive", ice="Fresh ice", espresso_martini=False,
        updrinks_q="Which drink is served up, and what does that mean for the glass?",
        updrinks_a="Chai Hard. Chilled coupe, no ice in the glass."),
}

# ------------------------------------------------------------------- styles
CSS = """
  :root {
    --bg:#F7F5EE; --card:#FFFFFF; --ink:#1B1B16; --muted:#5F5F55; --faint:#8E8E7C;
    --line:#D8D3C2; --rule:#BDB8A6; --hair:#EBE7D9;
    --accent:#33593F; --accent-ink:#2A4834; --accent-soft:#E7EFE8;
    --flag:#8A5A22; --flag-soft:#FBF1E2; --flag-line:#E3C79C;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg:#121309; --card:#1C1E15; --ink:#F1EEE1; --muted:#ACAA9B; --faint:#82806F;
      --line:#3A3D30; --rule:#4E5142; --hair:#2A2D22;
      --accent:#8FBE9C; --accent-ink:#B6D8BF; --accent-soft:#22301F;
      --flag:#E0AC72; --flag-soft:#2C2417; --flag-line:#4E3D24;
    }
  }
  :root[data-theme="dark"] {
    --bg:#121309; --card:#1C1E15; --ink:#F1EEE1; --muted:#ACAA9B; --faint:#82806F;
    --line:#3A3D30; --rule:#4E5142; --hair:#2A2D22;
    --accent:#8FBE9C; --accent-ink:#B6D8BF; --accent-soft:#22301F;
    --flag:#E0AC72; --flag-soft:#2C2417; --flag-line:#4E3D24;
  }

  * { box-sizing:border-box; }
  body { background:var(--bg); color:var(--ink); margin:0;
         font-family:'Inter',system-ui,-apple-system,sans-serif;
         font-size:15px; line-height:1.5; -webkit-font-smoothing:antialiased; }
  .wrap { max-width:840px; margin:0 auto; padding-inline:20px; padding-block:40px 64px; }

  .eyebrow { font-size:10.5px; font-weight:600; letter-spacing:.18em;
             text-transform:uppercase; color:var(--accent); margin:0 0 10px; }
  h1 { font-family:'Fraunces',Georgia,serif; font-weight:600;
       font-size:clamp(30px,6.5vw,42px); line-height:1.04; letter-spacing:-.02em;
       margin:0; text-wrap:balance; }
  .standard { margin:14px 0 0; font-size:15px; color:var(--muted); max-width:38em; }
  .standard b { color:var(--ink); font-weight:600; }

  /* candidate details */
  .details { margin-top:24px; padding:18px 20px; border:1.5px solid var(--ink);
             border-radius:3px; display:grid; gap:16px 26px;
             grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); }
  .field { display:flex; align-items:baseline; gap:10px; }
  .field .lab { flex:none; font-size:10px; font-weight:600; letter-spacing:.13em;
                text-transform:uppercase; color:var(--faint); }
  .field .ln { flex:1 1 auto; min-width:60px; border-bottom:1px solid var(--rule); height:19px; }
  .attempt { display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }
  .box { display:inline-block; width:13px; height:13px; border:1.5px solid var(--rule);
         border-radius:2px; vertical-align:-2px; margin-right:5px; }

  h2 { font-family:'Fraunces',Georgia,serif; font-weight:600; font-size:24px;
       margin:0; letter-spacing:-.01em; }
  .sec { margin-top:40px; }
  .sec-head { border-bottom:2px solid var(--ink); padding-bottom:9px;
              display:flex; align-items:flex-end; justify-content:space-between; gap:16px; }
  .sec-num { font-size:10.5px; font-weight:600; letter-spacing:.14em;
             text-transform:uppercase; color:var(--faint); display:block; margin-bottom:5px; }
  .sec-pts { flex:none; font-size:11px; font-weight:600; letter-spacing:.08em;
             text-transform:uppercase; color:var(--faint); white-space:nowrap; }
  .sec-note { margin:10px 0 0; font-size:13.5px; color:var(--muted); }

  /* spec blocks */
  .specs { margin-top:18px; display:grid; gap:16px;
           grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); }
  .spec { border:1px solid var(--line); border-radius:3px; padding:14px 15px 12px;
          background:var(--card); break-inside:avoid; }
  .spec h3 { font-family:'Fraunces',Georgia,serif; font-weight:600; font-size:17px;
             line-height:1.15; margin:0 0 10px; letter-spacing:-.01em; }
  .colhead { display:flex; gap:10px; font-size:9px; font-weight:600; letter-spacing:.13em;
             text-transform:uppercase; color:var(--faint); margin-bottom:3px; }
  .colhead .a { flex:none; width:58px; }
  .wrow { display:flex; gap:10px; margin-bottom:9px; }
  .wrow .a { flex:none; width:58px; border-bottom:1px solid var(--rule); height:20px; }
  .wrow .b { flex:1 1 auto; border-bottom:1px solid var(--rule); height:20px; }
  .frow { display:flex; align-items:baseline; gap:9px; margin-top:8px; }
  .frow .lab { flex:none; width:58px; text-align:right; font-size:9.5px; font-weight:600;
               letter-spacing:.1em; text-transform:uppercase; color:var(--faint); }
  .frow .ln { flex:1 1 auto; border-bottom:1px solid var(--rule); height:20px; }
  .score { margin-top:11px; padding-top:8px; border-top:1px solid var(--hair);
           display:flex; justify-content:flex-end; align-items:baseline; gap:7px;
           font-size:10px; font-weight:600; letter-spacing:.1em; text-transform:uppercase;
           color:var(--faint); }
  .score .slot { display:inline-block; width:30px; border-bottom:1px solid var(--rule);
                 height:16px; }

  /* questions */
  .qs { margin-top:18px; display:grid; gap:15px; counter-reset:q; }
  .q { counter-increment:q; break-inside:avoid; }
  .q p { margin:0 0 7px; font-size:14.5px; font-weight:500;
         display:flex; gap:10px; align-items:baseline; }
  .q p::before { content:counter(q); flex:none; font-family:'IBM Plex Mono',monospace;
                 font-size:10px; font-weight:600; color:var(--muted);
                 width:19px; height:19px; border:1px solid var(--line); border-radius:50%;
                 display:grid; place-items:center; transform:translateY(2px); }
  .ans { border-bottom:1px solid var(--rule); height:21px; margin-left:29px; }
  .ans + .ans { margin-top:9px; }

  /* practical checklist */
  table { width:100%; border-collapse:collapse; margin-top:16px; font-size:13.5px; }
  th { text-align:left; font-size:9.5px; font-weight:600; letter-spacing:.11em;
       text-transform:uppercase; color:var(--faint); padding:0 8px 7px;
       border-bottom:1.5px solid var(--ink); }
  th.c, td.c { text-align:center; width:74px; }
  td { padding:9px 8px; border-bottom:1px solid var(--hair); vertical-align:middle; }
  td.build { border-bottom:1px solid var(--rule); }

  .result { margin-top:26px; border:1.5px solid var(--ink); border-radius:3px; padding:18px 20px; }
  .result h3 { font-family:'Fraunces',Georgia,serif; font-size:18px; font-weight:600;
               margin:0 0 12px; }
  .tally { display:grid; gap:10px 26px;
           grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); }
  .tally .field .lab { width:auto; }
  .verdict { margin-top:16px; padding-top:14px; border-top:1px solid var(--line);
             display:flex; flex-wrap:wrap; gap:14px 30px; align-items:baseline;
             font-size:14px; font-weight:500; }
  .sign { margin-top:18px; display:grid; gap:18px 30px;
          grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); }

  .rule-note { margin-top:22px; background:var(--flag-soft); border:1px solid var(--flag-line);
               border-radius:3px; padding:14px 16px; break-inside:avoid; }
  .rule-note h4 { font-size:10px; font-weight:600; letter-spacing:.14em;
                  text-transform:uppercase; color:var(--flag); margin:0 0 6px; }
  .rule-note p { margin:0; font-size:14px; }

  /* answer key */
  .key { margin-top:26px; }
  .key-banner { background:var(--ink); color:var(--bg); border-radius:3px;
                padding:13px 16px; display:flex; flex-wrap:wrap; gap:6px 16px;
                align-items:baseline; justify-content:space-between; }
  .key-banner strong { font-size:13px; font-weight:600; letter-spacing:.13em;
                       text-transform:uppercase; }
  .key-banner span { font-size:12.5px; opacity:.82; }
  .key-grid { margin-top:16px; display:grid; gap:14px;
              grid-template-columns:repeat(auto-fit,minmax(290px,1fr)); }
  .key-card { border:1px solid var(--line); border-radius:3px; padding:12px 14px;
              background:var(--card); break-inside:avoid; }
  .key-card h3 { font-family:'Fraunces',Georgia,serif; font-size:15.5px; font-weight:600;
                 margin:0 0 8px; }
  .key-card dl { margin:0; display:grid; gap:4px; }
  .key-card .kr { display:flex; gap:9px; font-size:13px; align-items:baseline; }
  .key-card .kr dt { flex:none; width:52px; text-align:right; font-size:9.5px;
                     font-weight:600; letter-spacing:.09em; text-transform:uppercase;
                     color:var(--faint); }
  .key-card .kr dd { margin:0; }
  .key-card .amt { font-family:'IBM Plex Mono',monospace; font-weight:600;
                   font-variant-numeric:tabular-nums; color:var(--accent); }
  .key-qs { margin-top:16px; display:grid; gap:9px; }
  .key-q { font-size:13.5px; break-inside:avoid; }
  .key-q b { font-weight:600; }
  .key-q span { color:var(--muted); }

  footer { margin-top:44px; padding-top:16px; border-top:1px solid var(--line);
           color:var(--muted); font-size:13px; }

  @media print {
    @page { size:letter portrait; margin:0.5in 0.55in 0.45in; }
    :root, :root[data-theme="dark"] {
      --bg:#FFFFFF; --card:#FFFFFF; --ink:#141410; --muted:#4A4A40; --faint:#6E6E62;
      --line:#B6B2A2; --rule:#8E8A7A; --hair:#DEDACD;
      --accent:#2A4834; --accent-ink:#2A4834; --accent-soft:#E7EFE8;
      --flag:#6F4715; --flag-soft:#FBF1E2; --flag-line:#D5B682;
    }
    * { -webkit-print-color-adjust:exact; print-color-adjust:exact; }
    body { background:#fff; font-size:9.6pt; line-height:1.4; }
    .wrap { max-width:none; padding:0; }
    h1 { font-size:23pt; }
    .standard { font-size:9.5pt; margin-top:9pt; }
    .details { margin-top:13pt; padding:10pt 12pt; gap:11pt 20pt; }
    .sec { margin-top:20pt; }
    .sec h2 { font-size:15pt; }
    .sec-note { font-size:9pt; margin-top:6pt; }
    .specs { margin-top:11pt; gap:10pt; grid-template-columns:1fr 1fr; }
    .spec { padding:9pt 10pt 8pt; }
    .spec h3 { font-size:12pt; margin-bottom:7pt; }
    .wrow { margin-bottom:6pt; } .wrow .a, .wrow .b, .frow .ln { height:15pt; }
    .frow { margin-top:5pt; }
    .qs { margin-top:11pt; gap:10pt; }
    .q p { font-size:9.6pt; margin-bottom:5pt; }
    .ans { height:15pt; } .ans + .ans { margin-top:6pt; }
    table { margin-top:10pt; font-size:9pt; } td { padding:6pt; }
    .result { margin-top:16pt; padding:11pt 13pt; break-inside:avoid; }
    .sign { margin-top:12pt; }
    .rule-note { margin-top:13pt; padding:9pt 11pt; } .rule-note p { font-size:9pt; }
    .key-grid { grid-template-columns:1fr 1fr; gap:9pt; }
    .key-card { padding:8pt 10pt; } .key-card h3 { font-size:11pt; }
    .key-card .kr { font-size:8.6pt; }
    .key-q { font-size:8.8pt; }
    footer { margin-top:16pt; font-size:8.5pt; }
  }
"""


# ------------------------------------------------------------------ builder
def esc(t): return html.escape(t, quote=False)

def resolve(loc):
    """Drinks and questions for one location, with glassware substituted."""
    drinks = [d for d in DRINKS
              if not d.get('short_north_only') or loc['espresso_martini']]
    qs = list(QUESTIONS)
    if loc['espresso_martini']:
        qs.insert(4, EM_QUESTION)
    qs = [(q.format(updrinks_q=loc['updrinks_q']),
           a.format(updrinks_a=loc['updrinks_a'])) for q, a in qs]
    return drinks, qs

def scoring(drinks, qs):
    spec_pts = sum(len(d['pours']) + 2 for d in drinks)
    q_pts = len(qs) * 2
    written = spec_pts + q_pts
    return spec_pts, q_pts, written, -(-written * 90 // 100)   # ceil to 90%

def build_test(loc):
    drinks, qs = resolve(loc)
    spec_pts, q_pts, written, passmark = scoring(drinks, qs)

    specs = []
    for d in drinks:
        rows = ''.join('<div class="wrow"><span class="a"></span>'
                       '<span class="b"></span></div>' for _ in d['pours'])
        specs.append(
            '<div class="spec">\n'
            '          <h3>%s</h3>\n'
            '          <div class="colhead"><span class="a">Amount</span>'
            '<span>Ingredient</span></div>\n'
            '          %s\n'
            '          <div class="frow"><span class="lab">Glass</span>'
            '<span class="ln"></span></div>\n'
            '          <div class="frow"><span class="lab">Ice</span>'
            '<span class="ln"></span></div>\n'
            '          <div class="frow"><span class="lab">Garnish</span>'
            '<span class="ln"></span></div>\n'
            '          <div class="score"><span>Score</span><span class="slot"></span>'
            '<span>/ %d</span></div>\n'
            '        </div>' % (esc(d['name']), rows, len(d['pours']) + 2))

    qhtml = ''.join(
        '<div class="q"><p>%s</p><div class="ans"></div><div class="ans"></div></div>'
        % esc(q) for q, _ in qs)

    CHECKS = ["Correct glass, chilled or iced as specced",
              "Every pour measured — no free-pouring",
              "Correct build order", "Shaken hard until the tin frosts",
              "Correct garnish, placed cleanly",
              "Finished and on the rail within 2:00",
              "Station left clean"]
    rows = ''
    for n in (1, 2, 3):
        rows += ('<tr><td class="build" colspan="3"><b>Build %d</b> &nbsp; '
                 'Drink: <span style="display:inline-block;width:150px;'
                 'border-bottom:1px solid var(--rule)"></span>'
                 '&nbsp;&nbsp; Time: <span style="display:inline-block;width:62px;'
                 'border-bottom:1px solid var(--rule)"></span></td></tr>' % n)
        for c in CHECKS:
            rows += ('<tr><td>%s</td><td class="c"><span class="box"></span></td>'
                     '<td class="c"><span class="box"></span></td></tr>' % esc(c))

    return TEST_TEMPLATE.format(
        title=loc['title'], label=esc(loc['label']), css=CSS,
        specs='\n        '.join(specs), questions=qhtml, rows=rows,
        spec_pts=spec_pts, q_pts=q_pts, written=written, passmark=passmark)

def build_key(loc):
    drinks, qs = resolve(loc)
    spec_pts, q_pts, written, passmark = scoring(drinks, qs)

    def gl(d): return d['glass'].format(rocks=loc['rocks'])
    def ic(d): return d['ice'].format(ice=loc['ice'])

    keys = []
    for d in drinks:
        pours = ''.join(
            '<div class="kr"><dt><span class="amt">%s</span></dt><dd>%s</dd></div>'
            % (esc(a), esc(b)) for a, b in d['pours'])
        keys.append(
            '<div class="key-card">\n          <h3>%s</h3>\n          <dl>%s'
            '<div class="kr"><dt>Total</dt><dd>%s</dd></div>'
            '<div class="kr"><dt>Glass</dt><dd>%s</dd></div>'
            '<div class="kr"><dt>Ice</dt><dd>%s</dd></div>'
            '<div class="kr"><dt>Garnish</dt><dd>%s</dd></div></dl>\n        </div>'
            % (esc(d['name']), pours, esc(d['total']), esc(gl(d)), esc(ic(d)),
               esc(d['garnish'])))

    keyq = ''.join(
        '<div class="key-q"><b>%d. %s</b><span>%s</span></div>'
        % (i + 1, esc(q), esc(a)) for i, (q, a) in enumerate(qs))

    return KEY_TEMPLATE.format(
        title=loc['key_title'], label=esc(loc['label']), css=CSS,
        keys='\n        '.join(keys), keyq=keyq,
        spec_pts=spec_pts, q_pts=q_pts, written=written, passmark=passmark)

HEAD = """<meta charset="utf-8">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap">
<style>{css}</style>
"""

TEST_TEMPLATE = HEAD + """
<div class="wrap">

  <header>
    <p class="eyebrow">{label} &middot; Bar Certification</p>
    <h1>Fall Cocktail Certification</h1>
    <p class="standard">Closed book. No build sheet, no phone, no asking the
      bartender next to you. A bartender is certified on this menu at
      <b>{passmark} of {written} written points</b> and <b>three correct builds
      on the bar, each finished within 2:00</b>. Anything less is a re-test,
      not a pass.</p>
  </header>

  <div class="details">
    <div class="field"><span class="lab">Bartender</span><span class="ln"></span></div>
    <div class="field"><span class="lab">Date</span><span class="ln"></span></div>
    <div class="field"><span class="lab">Certifying manager</span><span class="ln"></span></div>
    <div class="field attempt"><span class="lab">Attempt</span>
      <span><span class="box"></span>First</span>
      <span><span class="box"></span>Re-test</span>
    </div>
  </div>

  <section class="sec">
    <div class="sec-head">
      <div><span class="sec-num">Section 1</span><h2>Write the spec</h2></div>
      <span class="sec-pts">{spec_pts} points</span>
    </div>
    <p class="sec-note">One point per correct line &mdash; the amount and the
      ingredient both have to be right. One point each for glass and garnish.
      Write amounts in ounces.</p>
    <div class="specs">
        {specs}
    </div>
  </section>

  <section class="sec">
    <div class="sec-head">
      <div><span class="sec-num">Section 2</span><h2>What gets sent back</h2></div>
      <span class="sec-pts">{q_pts} points</span>
    </div>
    <p class="sec-note">Two points each. These are the mistakes that actually
      come back to the bar.</p>
    <div class="qs">{questions}</div>
  </section>

  <section class="sec">
    <div class="sec-head">
      <div><span class="sec-num">Section 3</span><h2>Build it on the bar</h2></div>
      <span class="sec-pts">Pass / fail</span>
    </div>
    <p class="sec-note">The certifying manager picks three drinks at random and
      watches the full build. Start the clock when the ticket is called and stop
      it when the drink hits the rail &mdash; the standard is <b>2:00</b>, garnish
      included. Every line has to be checked for the build to count. One missed
      line is a failed build.</p>
    <table>
      <thead><tr><th>Checked on every build</th><th class="c">Pass</th><th class="c">Fail</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>

    <div class="rule-note">
      <h4>Automatic re-test</h4>
      <p>Wrong glass, wrong garnish, a missed ingredient, any free-poured
        measure, or a build over 2:00 fails that build outright, whatever the
        written score. Specs are not a matter of judgement.</p>
    </div>
  </section>

  <div class="result">
    <h3>Result</h3>
    <div class="tally">
      <div class="field"><span class="lab">Section 1</span><span class="ln"></span>
        <span class="lab">/ {spec_pts}</span></div>
      <div class="field"><span class="lab">Section 2</span><span class="ln"></span>
        <span class="lab">/ {q_pts}</span></div>
      <div class="field"><span class="lab">Written total</span><span class="ln"></span>
        <span class="lab">/ {written}</span></div>
      <div class="field"><span class="lab">Builds passed</span><span class="ln"></span>
        <span class="lab">/ 3</span></div>
    </div>
    <div class="verdict">
      <span><span class="box"></span>Certified &mdash; {passmark}+ written and 3 of 3 builds under 2:00</span>
      <span><span class="box"></span>Re-test &mdash; date set:
        <span style="display:inline-block;width:120px;border-bottom:1px solid var(--rule)"></span></span>
    </div>
    <div class="sign">
      <div class="field"><span class="lab">Bartender signature</span><span class="ln"></span></div>
      <div class="field"><span class="lab">Manager signature</span><span class="ln"></span></div>
    </div>
  </div>

  <footer>
    <p>Keep the signed sheet in the bartender's file. Re-certify the whole bar
      team whenever the menu changes.</p>
  </footer>

</div>
"""

KEY_TEMPLATE = HEAD + """
<div class="wrap">

  <header>
    <p class="eyebrow">{label} &middot; Bar Certification</p>
    <h1>Answer Key</h1>
  </header>

  <div class="key-banner">
    <strong>Manager copy</strong>
    <span>Grade from this sheet. It is printed separately from the test &mdash;
      keep it off the bar while anyone is being certified.</span>
  </div>

  <p class="standard">Section 1 is worth <b>{spec_pts}</b>, Section 2 <b>{q_pts}</b>,
    for <b>{written}</b> written points. A bartender certifies at <b>{passmark}</b>
    plus three correct builds, each finished within <b>2:00</b> from called ticket
    to the rail.</p>

  <section class="sec">
    <div class="sec-head">
      <div><span class="sec-num">Section 1</span><h2>The specs</h2></div>
      <span class="sec-pts">{spec_pts} points</span>
    </div>
    <p class="sec-note">One point per line, amount and ingredient both correct.
      One point each for glass and garnish. Ice is not scored on its own &mdash;
      it is checked on the bar in Section 3.</p>
    <div class="key-grid">
        {keys}
    </div>
  </section>

  <section class="sec">
    <div class="sec-head">
      <div><span class="sec-num">Section 2</span><h2>What gets sent back</h2></div>
      <span class="sec-pts">{q_pts} points</span>
    </div>
    <p class="sec-note">Two points each. Award the full two if they have the
      substance &mdash; the wording will not match.</p>
    <div class="key-qs">{keyq}</div>
  </section>

  <footer>
    <p>Specs change. Re-print this key whenever the build sheet changes, and
      re-certify the bar team.</p>
  </footer>

</div>
"""

if __name__ == '__main__':
    for key, loc in LOCATIONS.items():
        for kind, fn in (('certification', build_test), ('answer-key', build_key)):
            path = 'cocktail-%s-%s.html' % (kind, key)
            io.open(path, 'w', encoding='utf-8').write(fn(loc))
            print('wrote', path)
