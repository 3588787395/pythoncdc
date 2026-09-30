# -*- coding: utf-8 -*-
"""ab2.py <landed.jsonl> <cand.jsonl>   逐函数 mismatch 集合差（gained=变坏, lost=变好）。"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')


def load(f):
    d = {}
    for l in io.open(f, encoding='utf-8'):
        if l.strip():
            r = json.loads(l)
            d[r['path']] = r
    return d


A, B = load(sys.argv[1]), load(sys.argv[2])
for p in sorted(set(A) & set(B)):
    a, b = A[p], B[p]
    if a.get('error') or b.get('error'):
        print('ERR %s %s / %s' % (p, a.get('error'), b.get('error')))
        continue
    if a.get('sha') == b.get('sha'):
        continue
    sa = set(str(x) for x in (a.get('mism') or []))
    sb = set(str(x) for x in (b.get('mism') or []))
    gained = sorted(sb - sa)
    lost = sorted(sa - sb)
    if not gained and not lost:
        print('SHA-ONLY %s  %s/%s -> %s/%s' % (p, a['matched_functions'], a['total_functions'],
                                               b['matched_functions'], b['total_functions']))
        continue
    print('%s  %s/%s -> %s/%s' % (p.split('/')[-1], a['matched_functions'], a['total_functions'],
                                  b['matched_functions'], b['total_functions']))
    for x in gained:
        print('    + (worse) %s' % x)
    for x in lost:
        print('    - (better) %s' % x)
