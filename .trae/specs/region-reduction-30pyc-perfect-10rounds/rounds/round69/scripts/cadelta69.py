# -*- coding: utf-8 -*-
"""Per-candidate official-ruler delta for the R69 centre adjudication (read-only)."""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
G = r'D:/Temp/opencode/r69gate/center/dump/'


def load(p):
    d = {}
    for l in io.open(p, encoding='utf-8'):
        if l.strip():
            r = json.loads(l)
            d[r['path'].split('site-packages/')[-1]] = r
    return d


def tot(d):
    return (sum(len(r['mism']) for r in d.values()),
            sum(abs((m[1] or 0) - (m[2] or 0)) for r in d.values() for m in r['mism']),
            sum((m[3] or 0) for r in d.values() for m in r['mism']))


b = load(G + 'landed10.jsonl')
print('landed: defects=%d Sigma|d|=%d Sigmajumpdiff=%d' % tot(b))
for a in ('d1d', 'd2a', 'd5i'):
    c = load(G + '%s_all10.jsonl' % a)
    print('%s:   defects=%d Sigma|d|=%d Sigmajumpdiff=%d' % ((a,) + tot(c)))
    for k in sorted(b):
        bm, cm = b[k]['mism'], c[k]['mism']
        if bm == cm:
            continue
        print('   %s' % k)
        print('     landed %s' % bm)
        print('     cand   %s' % cm)
