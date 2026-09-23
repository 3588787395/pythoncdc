# -*- coding: utf-8 -*-
"""G5 落地态产物 vs 门禁臂产物逐字节比对（Round 51）。"""
import io
import json

BS = chr(92)


def load(p):
    d = {}
    for l in io.open(p, encoding='utf-8'):
        if l.strip():
            r = json.loads(l)
            d[r['path'].replace(BS, '/')] = r
    return d


L = load('D:/Temp/r51b/g5_landed.jsonl')
C = load('D:/Temp/r51b/g4_cand.jsonl')
H = load('D:/Temp/r51b/g4_head.jsonl')
same = diff = 0
for k in sorted(L):
    a, b, c = L[k], C.get(k), H.get(k)
    ok = bool(b) and a['sha'] == b['sha']
    same += 1 if ok else 0
    diff += 0 if ok else 1
    mv = 'MOVED-vs-head' if c and c['sha'] != a['sha'] else 'same-as-head'
    print('%-62s %-8s %-16s %s/%s %s' % (
        k.split('site-packages/')[-1][-62:], '==cand' if ok else '!=cand',
        a['sha'], a['matched_functions'], a['total_functions'], mv))
    if not ok:
        print('    cand=%s head=%s' % (b and b['sha'], c and c['sha']))
print('landed==cand: %d/%d, differing=%d' % (same, len(L), diff))
print('mism equal to cand:', all(L[k]['mism'] == C[k]['mism'] for k in L))
