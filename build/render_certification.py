#!/usr/bin/env python3
"""Render each certification sheet to PDF.

Two passes: the first measures which page the answer key lands on, the
second stamps that page range into the key banner so a manager printing
the test can't accidentally hand over the answers.
"""
import io, os, re, sys
from playwright.sync_api import sync_playwright
import pypdfium2 as pdfium

SCRATCH = sys.argv[1]
FONTS = io.open(SCRATCH + '/fonts-inline.css', encoding='utf-8').read()
FOOT = ('<div style="width:100%;font-family:Helvetica,Arial,sans-serif;font-size:7pt;'
        'color:#8A897C;padding:0 0.55in;display:flex;justify-content:space-between;">'
        '<span>__LABEL__ &middot; Fall Cocktail Certification</span>'
        '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')
MARGIN = {'top': '0.5in', 'bottom': '0.6in', 'left': '0.55in', 'right': '0.55in'}

def render(browser, html, out, label):
    html = re.sub(r'<link rel="preconnect"[^>]*>\n', '', html)
    html = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^"]*">\n', '', html)
    tmp = '.cert-build.html'
    io.open(tmp, 'w', encoding='utf-8').write(html.replace('<style>', '<style>\n' + FONTS + '\n', 1))
    pg = browser.new_page()
    pg.goto('file://' + os.path.abspath(tmp), wait_until='load')
    pg.emulate_media(media='print'); pg.wait_for_timeout(1400)
    pg.pdf(path=out, format='Letter', print_background=True, display_header_footer=True,
           header_template='<div></div>', footer_template=FOOT.replace('__LABEL__', label),
           margin=MARGIN)
    pg.close(); os.remove(tmp)

def key_page(path):
    pdf = pdfium.PdfDocument(path)
    for i in range(len(pdf)):
        if 'ANSWER KEY' in pdf[i].get_textpage().get_text_range().upper():
            return i + 1, len(pdf)
    raise SystemExit('answer key page not found in ' + path)

for key, label in [('short-north', 'TownHall Short North'),
                   ('ohio-city', 'TownHall Ohio City')]:
    stem = 'cocktail-certification-' + key
    src = io.open(stem + '.html', encoding='utf-8').read()
    with sync_playwright() as pw:
        b = pw.chromium.launch(
            executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
            args=['--no-sandbox'])
        render(b, src.replace('__LASTTESTPAGE__', '?'), stem + '.pdf', label)
        kp, total = key_page(stem + '.pdf')
        final = src.replace('__LASTTESTPAGE__', str(kp - 1))
        io.open(stem + '.html', 'w', encoding='utf-8').write(final)
        render(b, final, stem + '.pdf', label)
        b.close()
    print('%-44s %d pages  test 1-%d, key %d-%d' % (stem + '.pdf', total, kp - 1, kp, total))
