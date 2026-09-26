# -*- coding: utf-8 -*-
"""Re-derive G1 (56-target official tally) and G4p (48-file strict tally) with
FULL repo-relative keys: gates71a keyed rows by basename@parent, which collided on
exception.pyc@utils and api_base.pyc@api (2 of 56 rows lost) and on one 31-function
row of the strict 48 (ok totals 1745/1749 instead of 1776/1780).  Same rules,
same dumps, no other gate file is touched."""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'D:/Temp/opencode/r71gate/center'
D = os.path.join(ROOT, 'dump')
G = os.path.join(ROOT, 'logs')


def jload(p):
    return [json.loads(l) for l in io.open(p, encoding='utf-8') if l.strip()]


def rel(p):
    q = p.replace('\\', '/')
    return q.split('site-packages/')[-1] if 'site-packages/' in q else q


def delta(m):
    try:
        return abs((m[1] or 0) - (m[2] or 0))
    except Exception:
        return 0


A = {rel(r['path']): r for r in jload(os.path.join(D, 'landed56_r71.jsonl'))}
B = {rel(r['path']): r for r in jload(os.path.join(D, 'm71_56.jsonl'))}
assert len(A) == 56 == len(B), (len(A), len(B))
tally = {'IMPROVED': 0, 'SAME': 0, 'MOVED': 0, 'REGRESSION': 0, 'ERR': 0}
L = ['G1 official ruler on the 56 pylingual-failure targets (landed -> m71)', '=' * 70]
L.append('(full repo-relative keys: basename@parent collided on exception.pyc@utils and')
L.append(' api_base.pyc@api in the first render, which dropped 2 of 56 rows)')
for k in sorted(A):
    a, b = A[k], B[k]
    if a.get('error') or b.get('error'):
        tally['ERR'] += 1
        L.append('%-64s ERR' % k)
        continue
    da, db = len(a['mism']), len(b['mism'])
    sa, sb = sum(delta(m) for m in a['mism']), sum(delta(m) for m in b['mism'])
    if db < da:
        v = 'IMPROVED'
    elif db > da:
        v = 'REGRESSION'
    elif a['mism'] == b['mism']:
        v = 'SAME' if a.get('sha') == b.get('sha') else 'MOVED'
    else:
        v = 'MOVED'
    tally[v] += 1
    L.append('%-64s %3d/%-3d d=%-3d |d|=%-4d -> %3d/%-3d d=%-3d |d|=%-4d  %s'
             % (k, a['matched_functions'], a['total_functions'], da, sa,
                b['matched_functions'], b['total_functions'], db, sb, v))
L.append('')
L.append('TALLY %s' % ' '.join('%s=%d' % kv for kv in sorted(tally.items())))
L.append('files fully matched: a=%d b=%d' % (
    sum(1 for r in A.values() if not r['mism']),
    sum(1 for r in B.values() if not r['mism'])))
io.open(os.path.join(G, 'G1_targets_r71.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G1] written', tally)

SA = {rel(r['pyc']): r for r in json.load(io.open(os.path.join(D, 'strict_landed_r71.json'),
                                                  encoding='utf-8'))}
SB = {rel(r['pyc']): r for r in json.load(io.open(os.path.join(D, 'strict_m71_r71.json'),
                                                  encoding='utf-8'))}
assert len(SA) == 48 == len(SB), (len(SA), len(SB))
L = ['G4p strict ruler on the 48 divergence targets (landed -> m71)', '=' * 70]
L.append('(full repo-relative keys: one 31-function row was lost to a basename@parent')
L.append(' collision in the first render, which read ok 1745 -> 1749)')
ok_a = ok_b = da = db = 0
t2 = {'SAME': 0, 'IMPROVED': 0, 'REGRESSION': 0}
for k in sorted(SA):
    a, b = SA[k], SB[k]
    ca, cb = len(a['bad']), len(b['bad'])
    ok_a += a['ok']; ok_b += b['ok']; da += ca; db += cb
    if cb > ca or b['ok'] < a['ok']:
        v = 'REGRESSION'
    elif cb < ca or b['ok'] > a['ok']:
        v = 'IMPROVED'
    else:
        v = 'SAME'
    t2[v] += 1
    L.append('%-64s ok %3d/%-3d d=%-3d -> ok %3d/%-3d d=%-3d  %s'
             % (k, a['ok'], a['functions'], ca, b['ok'], b['functions'], cb, v))
L.append('')
L.append('TALLY %s' % ' '.join('%s=%d' % kv for kv in sorted(t2.items())))
def _bad(d):
    out = {}
    for k, r in d.items():
        for b in r['bad']:
            out.setdefault((k if isinstance(b, str) else b.get('name', str(b))), 0)
    return out


def _names(r):
    def one(x):
        if isinstance(x, str):
            return x
        if isinstance(x, (list, tuple)):
            return str(x[0])
        if isinstance(x, dict):
            return str(x.get('name', x))
        return str(x)
    return set(one(x) for x in r['bad'])


fa = {k: _names(v) for k, v in SA.items()}
fb = {k: _names(v) for k, v in SB.items()}
newf = sorted(k for k in fb if fb[k] - fa.get(k, set()))
fixf = sorted(k for k in fa if fa[k] - fb.get(k, set()))
L.append('NEW defect functions=%d  FIXED defect functions=%d  %s'
         % (len(newf), len(fixf), 'NEW=%s FIXED=%s' % (newf, fixf) if (newf or fixf) else ''))
L.append('STRICT TOTAL ok %d -> ok %d (of %d/%d) ; defects %d -> %d'
         % (ok_a, ok_b, sum(r['functions'] for r in SA.values()),
            sum(r['functions'] for r in SB.values()), da, db))
io.open(os.path.join(G, 'G4p_strict_after_r71.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G4p] written ok %d -> %d, defects %d -> %d  %s' % (ok_a, ok_b, da, db, t2))
