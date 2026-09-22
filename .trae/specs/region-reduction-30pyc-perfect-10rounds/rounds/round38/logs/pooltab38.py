# -*- coding: utf-8 -*-
"""Round 38 function-level pool table (forked from d1tab37.py, but over all 27 partial files).

Reads a landed-arm jsonl produced by r38c.py run and prints
  (a) every mismatching function sorted by |delta| then name,
  (b) clusters by (delta, jump_diffs, true_diffs) signature -> how many functions share a shape.

usage: python -X utf8 pooltab38.py --in=p27_landed.jsonl
"""
import io
import json
import sys
from collections import defaultdict

kw = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
sys.stdout.reconfigure(encoding='utf-8')
rows = [json.loads(l) for l in io.open(kw['in'], encoding='utf-8') if l.strip()]
assert len(rows) == 27, len(rows)
assert not [r for r in rows if r.get('error')], [r for r in rows if r.get('error')]

fn = []
for r in rows:
    f = r['path'].replace('\\', '/').split('site-packages/')[-1]
    for name, o, d, j, t in r['mism']:
        fn.append((f, name, o, d, j, t))

print('partial files %d   mismatching functions %d   sum|deficit| %d   sum(deficit>0) %d'
      % (len(rows), len(fn), sum(max(0, o - d) for _, _, o, d, _, _ in fn),
         sum(o - d for _, _, o, d, _, _ in fn)))
print('\n=== every mismatching function, sorted by |delta| ===')
for f, name, o, d, j, t in sorted(fn, key=lambda x: (-abs(x[2] - x[3]), x[0])):
    print('  %-68s %-32s %5d/%-5d delta %+5d  j%-3d t%d'
          % (f, name, o, d, d - o, j, t))

sig = defaultdict(list)
for f, name, o, d, j, t in fn:
    sig[(o - d, len(str(j)), j == 0)].append((f, name, o, d, j, t))
print('\n=== deficit-amount clusters (same |missing instructions|) ===')
byd = defaultdict(list)
for f, name, o, d, j, t in fn:
    byd[o - d].append((f, name, j, t))
for k in sorted(byd, key=lambda k: -abs(k)):
    v = byd[k]
    if len(v) >= 2:
        print('  delta %+4d : %d functions  %s' % (k, len(v), ', '.join(
            '%s::%s' % (a.split('/')[-1][:-4], b) for a, b, _, _ in v)))
