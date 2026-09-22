# -*- coding: utf-8 -*-
"""Corpus exposure: which landed partial files carry the transposition shape?

Signature under the STRICT ruler, computed from the landed sweep records only
(no decompilation, the sweep already stored (func, len_orig, len_decomp, n_hunks)):
  * equal-length defective function with >= 2 non-equal hunks  -> pure transposition
  * |len_o - len_d| >= 20 with >= 2 hunks                      -> big delete + insert family
Also cross-tabulates how those same functions behave under the R37-B mirrored arm.
"""
import glob
import json
import os
import sys

OUT = r'D:/Temp/r37diagB/out'
sys.stdout.reconfigure(encoding='utf-8')


def load(arm):
    recs = {}
    for p in sorted(glob.glob(os.path.join(OUT, 'sweep', arm, 'shard*.jsonl'))):
        for line in open(p, encoding='utf-8'):
            if line.strip():
                r = json.loads(line)
                recs[r['file'].replace('\\', '/')] = r
    return recs


L = load('landed')
try:
    M = load('mirrorB')
except Exception:
    M = {}
print('landed=%d  R37B-arm=%d' % (len(L), len(M)))

rows = []
for f, r in sorted(L.items()):
    for k, lo, ld, nh in (r.get('bad') or []):
        d = ld - lo
        shape = None
        if lo == ld and nh >= 2:
            shape = 'EQ-TRANSPOSE'
        elif abs(d) >= 20 and nh >= 2:
            shape = 'BIG-DEL+INS'
        elif abs(d) >= 20:
            shape = 'BIG-DEL-ONLY'
        if shape:
            mb = ''
            for kk, a, b, nn in ((M.get(f) or {}).get('bad') or []):
                if kk == k:
                    mb = 'R37B: len=%s hunk=%s cost=%s' % (b, nn, (M.get(f) or {}).get('strict_cost'))
                    break
            else:
                if f in M:
                    mb = 'R37B: FIXED(this func)'
            rows.append((shape, f, k, lo, ld, nh, mb))

for shape in ('EQ-TRANSPOSE', 'BIG-DEL+INS', 'BIG-DEL-ONLY'):
    sel = [x for x in rows if x[0] == shape]
    print('\n== %s : %d functions in %d files' % (shape, len(sel), len({x[1] for x in sel})))
    for s, f, k, lo, ld, nh, mb in sorted(sel, key=lambda x: -(x[3] + x[4])):
        print('  %-14s %-56s %4d/%4d h=%2d  %s' % (
            shape, f.replace('F:/Downloads/pythoncdc-main/site-packages/', '')[:56] + '::' + k.split('.')[-1][:18],
            lo, ld, nh, mb))

# files fully fixed by R37-B
fixed = [(f, L[f].get('strict_cost'), M[f].get('strict_cost')) for f in L if f in M
         and (M[f].get('strict_cost') or 0) == 0 and (L[f].get('strict_cost') or 0) > 0]
print('\n== files whose WHOLE strict cost is driven to 0 by R37-B: %d' % len(fixed))
for f, a, b in fixed:
    print('   %-70s %s -> %s' % (f.replace('F:/Downloads/pythoncdc-main/site-packages/', ''), a, b))
imp = sorted([(M[f]['strict_cost'] - L[f]['strict_cost'], f) for f in L if f in M
              and M[f].get('strict_cost') is not None and L[f].get('strict_cost') is not None])[:8]
print('\n== top improvements / regressions (delta, file)')
for d, f in imp:
    print('   %+5d %s' % (d, f.replace('F:/Downloads/pythoncdc-main/site-packages/', '')))
