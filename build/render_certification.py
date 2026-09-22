#!/usr/bin/env python3
"""Render the certification test and its answer key to PDF, per location.

The key is a separate document so it can be printed on its own and kept
off the bar; nothing about the test's pagination can leak the answers.
"""
import io, os, re, sys
from playwright.sync_api import sync_playwright
import pypdfium2 as pdfium

SCRATCH = sys.argv[1]
FONTS = io.open(SCRATCH + '/fonts-inline.css', encoding='utf-8').read()
FOOT = ('<div style="width:100%;font-family:Helvetica,Arial,sans-serif;font-size:7pt;'
        'color:#8A897C;padding:0 0.55in;display:flex;justify-content:space-between;">'
        '<span>__LABEL__</span>'
        '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')

DOCS = [
    ('cocktail-certification-short-north', 'TownHall Short North &middot; Fall Cocktail Certification'),
    ('cocktail-answer-key-short-north',    'TownHall Short North &middot; Certification Answer Key &mdash; manager copy'),
    ('cocktail-certification-ohio-city',   'TownHall Ohio City &middot; Fall Cocktail Certification'),
    ('cocktail-answer-key-ohio-city',      'TownHall Ohio City &middot; Certification Answer Key &mdash; manager copy'),
]

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
        args=['--no-sandbox'])
    for stem, label in DOCS:
        html = io.open(stem + '.html', encoding='utf-8').read()
        html = re.sub(r'<link rel="preconnect"[^>]*>\n', '', html)
        html = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^"]*">\n', '', html)
        tmp = '.cert-build.html'
        io.open(tmp, 'w', encoding='utf-8').write(
            html.replace('<style>', '<style>\n' + FONTS + '\n', 1))
        pg = browser.new_page()
        pg.goto('file://' + os.path.abspath(tmp), wait_until='load')
        pg.emulate_media(media='print'); pg.wait_for_timeout(1400)
        pg.pdf(path=stem + '.pdf', format='Letter', print_background=True,
               display_header_footer=True, header_template='<div></div>',
               footer_template=FOOT.replace('__LABEL__', label),
               margin={'top': '0.5in', 'bottom': '0.6in', 'left': '0.55in', 'right': '0.55in'})
        pg.close(); os.remove(tmp)
        pdf = pdfium.PdfDocument(stem + '.pdf')
        leaked = [i + 1 for i in range(len(pdf))
                  if 'ANSWER KEY' in pdf[i].get_textpage().get_text_range().upper()]
        if 'certification' in stem and leaked:
            raise SystemExit('answer key text found in the test: %s page %s' % (stem, leaked))
        print('%-42s %d pages' % (stem + '.pdf', len(pdf)))
    browser.close()
