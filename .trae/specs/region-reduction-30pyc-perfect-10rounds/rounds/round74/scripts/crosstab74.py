# -*- coding: utf-8 -*-
"""R74 center: cross-tab family x try-region x verdict for the 77 failing units."""
import io, json, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
C = r'D:/Temp/opencode/r74gate/center/'
fam = json.load(io.open(r'D:/Temp/opencode/r74gate/diag1/fam74_r74.json', encoding='utf-8'))
fd = io.open(C + 'dump/firstdiv73.txt', encoding='utf-8').read().splitlines()

inside = {}   # (file, func) -> origTryDepth
kind = {}     # (file, func) -> verdict kind
for l in fd:
    parts = [p.strip() for p in l.split('|')]
    if len(parts) < 5:
        continue
    f = parts[0]
    func = parts[1].split('.')[-1] if '.' in parts[1] else parts[1]
    # func column like <module>.Quote.get_price
    func_full = parts[1]
    m = re.search(r'origTryDepth=(\d+)', l)
    if m:
        inside[(f, func_full)] = int(m.group(1))
    kind[(f, func_full)] = parts[2]

def norm(name):
    return name

tab = collections.Counter()
rows = []
for r in fam:
    f = r['file']
    key = ('***<module>.' + r['name']) if False else None
    # fam records carry bare function name; firstdiv carries dotted path -> match by suffix
    match = None
    for k in inside:
        if k[0] == f and (k[1].endswith('.' + r['name']) or k[1] == r['name']):
            match = k
            break
    depth = inside.get(match, None)
    vk = kind.get(match, '?')
    row = {'file': f, 'name': r['name'], 'family': r['family'], 'verdict': r['verdict'],
           'trydepth': depth, 'inside': (depth or 0) > 0, 'fdkind': vk}
    rows.append(row)
    tab[(r['family'], 'IN' if (depth or 0) > 0 else ('OUT' if depth is not None else '?'))] += 1

print('== family x try-region ==')
for k in sorted(tab, key=lambda x: -tab[x]):
    print('  %-12s %-3s %d' % (k[0], k[1], tab[k]))
print('matched firstdiv rows: %d / %d' % (sum(1 for r in rows if r['trydepth'] is not None), len(rows)))

print('\n== inside-try units (fix3 target) ==')
for r in rows:
    if r['inside']:
        print('  %-60s %-12s %s' % (r['file'] + ' :: ' + r['name'], r['family'], r['fdkind']))

print('\n== F-PAD / F-POLARITY / F-OTHER units (fix2 target) ==')
for r in rows:
    if r['family'] in ('F-PAD', 'F-POLARITY', 'F-OTHER'):
        print('  %-60s %-12s inside=%s %s' % (r['file'] + ' :: ' + r['name'], r['family'],
                                              r['inside'], r['fdkind']))

print('\n== F-ABSORB by file ==')
per = collections.Counter(r['file'] for r in rows if r['family'] == 'F-ABSORB')
for f, n in per.most_common():
    print('  %-70s %d' % (f, n))

out = C + 'dump/crosstab74.txt'
io.open(out, 'w', encoding='utf-8', newline='\n').write(
    '\n'.join('%s\t%s\t%s\t%s\t%s\t%s' % (r['file'], r['name'], r['family'], r['verdict'],
                                          r['trydepth'], r['fdkind']) for r in rows) + '\n')
print('WROTE', out)
