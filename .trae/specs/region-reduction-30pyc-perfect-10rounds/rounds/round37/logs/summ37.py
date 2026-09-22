# -*- coding: utf-8 -*-
"""Summarise the round-37 whole-corpus crash scan and print the pool's per-function readings."""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
R37 = r'D:/Temp/r37gate/r37/'
LOG = r'F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round36/logs/'

rows = [l.rstrip('\n').split('\t') for l in io.open(R37 + 'scan37_all402.txt', encoding='utf-8') if l.strip()]
print('scan rows %d   sum-secs %.0f' % (len(rows), sum(float(r[1]) for r in rows)))
fatal = [r for r in rows if len(r) > 2 and r[2]]
rep = [r for r in rows if len(r) > 3 and r[3] != '-']
print('files with a file-level FATAL: %d' % len(fatal))
print('files with a swallowed exception / degradation entry: %d' % len(rep))
for r in rep:
    print('   %s -> %s' % (r[0], r[3]))
agg = {}
for r in rep:
    for part in r[3].split(';'):
        k = part.strip()
        agg[k] = agg.get(k, 0) + 1
for k, v in sorted(agg.items(), key=lambda x: -x[1]):
    print('  %4d  %s' % (v, k))
print()
print('slowest 5 files: %s' % ', '.join('%s %.1fs' % (r[0].split('/')[-1], float(r[1]))
                                        for r in sorted(rows, key=lambda r: -float(r[1]))[:5]))

for tag, fn in (('deficit-1', 'landed_d1.jsonl'), ('deficit-2', 'landed_d2.jsonl')):
    print('=== %s pool (%s) ===' % (tag, fn))
    for l in io.open(LOG + fn, encoding='utf-8'):
        e = json.loads(l)
        p = (e.get('pyc') or e.get('path') or '')
        print('  %-62s %s/%s  %s' % (p.replace('\\', '/').split('site-packages/')[-1],
                                     e.get('matched_functions'), e.get('total_functions'),
                                     e.get('mism')))
