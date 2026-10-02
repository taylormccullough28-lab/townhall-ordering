#!/usr/bin/env python3
"""Render a one-screen 'quick builds' image per location, for Toast handhelds.

Built from the same DRINKS table as the certification, so it cannot drift
from the build sheets. Output is a portrait PNG at 1080x1920 — it scales
down cleanly to a 5.5" handheld and stays legible at arm's length.
"""
import io, os, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_certification import LOCATIONS, resolve

W, H = 1080, 1920

# Short labels: a handheld has no room for "Coupe / martini — served up".
GLASS_SHORT = {
    'Rocks': 'Rocks', 'Emulsive': 'Emulsive',
    'Rocks — Pernod-rinsed': 'Rocks · rinsed',
    'Emulsive — Pernod-rinsed': 'Emulsive · rinsed',
    'Coupe / martini': 'Coupe · up', 'Martini coupe': 'Coupe · up',
    '12 oz tall': '12oz tall', 'Wine': 'Wine',
}
METHOD = {'Scarlett Spritz': 'BUILD', 'Chai Hard': 'UP', 'Espresso Martini': 'UP',
          'No New Friends': 'TOP'}

def esc(t): return html.escape(t, quote=False)

def short_ing(s):
    s = s.split('—')[0].strip()
    return {'Liquor of choice': 'Liquor — ask guest',
            'Pernod': 'Pernod — rinse glass'}.get(s, s)

def card(d, loc):
    rows = ''.join(
        '<div class="r"><span class="a">%s</span><span class="i">%s</span></div>'
        % (esc(a), esc(short_ing(b))) for a, b in d['pours'])
    glass = d['glass'].format(rocks=loc['rocks'])
    tag = METHOD.get(d['name'], 'SHAKE')
    return ('<div class="c">'
            '<div class="h"><span class="n">%s</span><span class="t t-%s">%s</span></div>'
            '%s'
            '<div class="f"><b>%s</b>%s</div>'
            '</div>' % (esc(d['name']), tag.lower(), tag, rows,
                        esc(GLASS_SHORT.get(glass, glass)), esc(d['garnish'])))

CSS = """
 *{box-sizing:border-box;margin:0;padding:0}
 body{width:%(W)spx;height:%(H)spx;background:#fff;color:#14140E;
      font-family:'Inter',system-ui,sans-serif;display:flex;flex-direction:column;
      padding:26px 24px 20px}
 header{border-bottom:5px solid #14140E;padding-bottom:14px;display:flex;
        align-items:flex-end;justify-content:space-between;gap:16px}
 h1{font-family:'Fraunces',Georgia,serif;font-size:50px;font-weight:600;
    letter-spacing:-.02em;line-height:1}
 .loc{font-size:21px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
      color:#33593F;margin-bottom:9px}
 .meta{text-align:right;font-size:20px;line-height:1.35;color:#53534A;font-weight:500}
 .meta b{color:#14140E}
 .grid{flex:1;display:grid;grid-template-columns:1fr 1fr;
       grid-auto-rows:1fr;gap:16px;margin-top:18px}
 .c{border:2px solid #CFCABA;border-radius:8px;padding:15px 17px 13px;
    display:flex;flex-direction:column}
 .h{display:flex;align-items:baseline;gap:10px;margin-bottom:11px}
 .n{font-family:'Fraunces',Georgia,serif;font-size:31px;font-weight:600;
    line-height:1.05;letter-spacing:-.01em;flex:1}
 .t{flex:none;font-size:16px;font-weight:600;letter-spacing:.09em;
    padding:4px 9px;border-radius:4px;background:#E7EFE8;color:#2A4834}
 .t-up{background:#EDE7F3;color:#4A3A63}
 .t-build,.t-top{background:#F8EBD8;color:#7A4E1C}
 .r{display:flex;gap:13px;align-items:baseline;padding:5px 0;
    border-bottom:1px solid #EFEBDE}
 .r:last-of-type{border-bottom:none}
 .a{flex:none;width:92px;text-align:right;font-family:'IBM Plex Mono',monospace;
    font-size:29px;font-weight:600;color:#2A4834;font-variant-numeric:tabular-nums}
 .i{font-size:27px;font-weight:500;line-height:1.2}
 .f{margin-top:auto;padding-top:11px;border-top:2px solid #14140E;
    font-size:21px;color:#53534A;line-height:1.3}
 .f b{color:#14140E;font-weight:600}
 .f b::after{content:' · '}
 .note{border:2px dashed #CFCABA;border-radius:8px;padding:17px;
       display:flex;flex-direction:column;justify-content:center;gap:9px}
 .note b{font-family:'Fraunces',Georgia,serif;font-size:27px;font-weight:600}
 .note span{font-size:21px;color:#53534A;line-height:1.35}
 footer{margin-top:16px;font-size:20px;color:#6E6E62;display:flex;
        justify-content:space-between;gap:16px}
""" % {'W': W, 'H': H}

PAGE = """<meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@600&display=swap">
<style>%s</style>
<header>
  <div><div class="loc">%s</div><h1>Quick Builds</h1></div>
  <div class="meta">All amounts in <b>oz</b><br>Every drink out in <b>2:00</b></div>
</header>
<div class="grid">%s</div>
<footer><span>Full specs on the build sheet</span><span>%s</span></footer>
"""

def build(loc):
    drinks, _ = resolve(loc)
    cells = [card(d, loc) for d in drinks]
    if len(cells) % 2:                      # odd count leaves a hole — use it
        cells.append('<div class="note"><b>Measure every pour</b>'
                     '<span>No free-pouring the biz. Wrong glass or wrong '
                     'garnish means it goes back.</span></div>')
    return PAGE % (CSS, esc(loc['label'].upper()), ''.join(cells),
                   esc('%d drinks' % len(drinks)))

if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    scratch = sys.argv[1]
    fonts = io.open(scratch + '/fonts-inline.css', encoding='utf-8').read()
    with sync_playwright() as pw:
        b = pw.chromium.launch(
            executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
            args=['--no-sandbox'])
        for key, loc in LOCATIONS.items():
            page_html = build(loc)
            offline = page_html.replace(
                '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
                'family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600'
                '&family=IBM+Plex+Mono:wght@600&display=swap">', '')
            offline = offline.replace('<style>', '<style>\n' + fonts + '\n', 1)
            tmp = '.qb.html'; io.open(tmp, 'w', encoding='utf-8').write(offline)
            pg = b.new_page(viewport={'width': W, 'height': H},
                            device_scale_factor=1)
            pg.goto('file://' + os.path.abspath(tmp), wait_until='load')
            pg.wait_for_timeout(900)
            out = 'quick-builds-%s.png' % key
            pg.screenshot(path=out)
            pg.close(); os.remove(tmp)
            print('%-32s %d x %d  %d KB'
                  % (out, W, H, os.path.getsize(out) // 1024))
        b.close()
