#!/usr/bin/env python3
"""Cross-check the build sheets against the certification spec table.

The build sheets are hand-maintained HTML; the certification and its
answer key are generated from DRINKS in make_certification.py. Nothing
links the two, so a spec edited in one place can silently disagree with
the other. This compares every drink in both directions and exits
non-zero on any mismatch.
"""
import io, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_certification import DRINKS, LOCATIONS, resolve

def from_build_sheet(path):
    """{drink name: (pours, total)} as the build sheet actually prints them."""
    s = io.open(path, encoding='utf-8').read()
    out = {}
    for m in re.finditer(r'<h3>(.*?)</h3>(.*?)</article>', s, re.S):
        name, card = m.group(1).strip(), m.group(2)
        pours = [(a, re.sub(r'<.*', '', b).strip())
                 for a, b in re.findall(
                     r'<span class="qty">([^<]*?)\s*(?:<span class="u">oz</span>)?</span>'
                     r'<span class="what">(.*?)</span>', card, re.S)]
        # Some amounts live in the numbered build steps rather than a pour
        # row: Scarlett Spritz is built in the glass, and the No New Friends
        # soda is an unmeasured top. Scan only the steps, never the total.
        steps = ''.join(re.findall(r'<ol class="steps">(.*?)</ol>', card, re.S))
        for amt, ing in re.findall(r'<b>([\d.]+) oz ([^<]*?)</b>', steps):
            pours.append((amt, ing.strip()))
        if re.search(r'Top with soda water', steps):
            pours.append(('top', 'Soda water'))
        total = re.search(r'Total pour <b>([^<]*)</b>', card)
        out[name] = (pours, total.group(1) if total else None)
    return out

def norm(s):
    """Compare on substance: drop the explanatory tail after an em dash."""
    return re.sub(r'\s+', ' ', s.split('—')[0]).strip().lower()

fails = 0
for key, loc in LOCATIONS.items():
    sheet = from_build_sheet('cocktail-build-sheet-%s.html' % key)
    drinks, _ = resolve(loc)
    for d in drinks:
        name = d['name']
        if name not in sheet:
            print('MISSING  %-11s %s not on the build sheet' % (key, name)); fails += 1; continue
        got_pours, got_total = sheet[name]
        want = [(a, norm(b)) for a, b in d['pours']]
        got = [(a, norm(b)) for a, b in got_pours]
        if want != got:
            print('POURS    %-11s %s\n           cert  %s\n           sheet %s'
                  % (key, name, want, got)); fails += 1
        if got_total and got_total != d['total']:
            print('TOTAL    %-11s %s  cert %s vs sheet %s'
                  % (key, name, d['total'], got_total)); fails += 1
    extra = set(sheet) - {d['name'] for d in drinks}
    for name in sorted(extra):
        print('EXTRA    %-11s %s on the build sheet but not in the cert' % (key, name)); fails += 1

    # every pour should add up to the stated total
    for d in drinks:
        nums = [float(a) for a, _ in d['pours'] if re.fullmatch(r'[\d.]+', a)]
        stated = float(re.match(r'([\d.]+)', d['total']).group(1))
        if abs(sum(nums) - stated) > 0.001:
            print('ARITH    %-11s %s  pours sum to %.2f, total says %s'
                  % (key, d['name'], sum(nums), d['total'])); fails += 1

print('\n%s' % ('%d mismatch(es)' % fails if fails else 'All specs agree across both editions.'))
sys.exit(1 if fails else 0)
