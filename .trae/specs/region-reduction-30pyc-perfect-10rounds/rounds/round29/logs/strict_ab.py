# -*- coding: utf-8 -*-
"""Strict-ruler A/B over the files whose product bytes moved in the 402-file gate.

The shipping A/B projects only (orig_count, decomp_count, jump_diffs, true_diffs)
per mismatched function and therefore cannot see an equal-length relocation, and
R97 trims spurious intermediate returns on the official ruler. This script loads
the repo's own strict ruler (_r10_strict_check) and, for each pyc, reports per arm:
  clean = #functions with no strict defect at all
  seqlen = #functions whose filtered length differs
  sigma  = sum |len(orig) - len(decomp)| over all functions
so a MOVED product can be shown strict-neutral, not just officially neutral.

usage: python -X utf8 strict_ab.py <list-of-pyc>
"""
import io
import json
import os
import sys
import importlib.util

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r29gate'
sys.stdout.reconfigure(encoding='utf-8')

_s = importlib.util.spec_from_file_location('r10', os.path.join(REPO, '_r10_strict_check.py'))
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)


def prod(arm, pyc):
    rel = pyc.replace('\\', '/')
    r0 = REPO.replace('\\', '/') + '/site-packages/'
    if rel.startswith(r0):
        rel = rel[len(r0):]
    return os.path.join(ROOT, 'build_' + arm,
                        rel.replace('/', '__')[:-4].replace(':', '_') + 'OK.py').replace('\\', '/')


def measure(pyc, ok):
    orig = r10._load_map(pyc)
    dec = r10._compile_map(ok)
    clean = seqlen = sigma = 0
    rows = []
    for k, c in orig.items():
        d = dec.get(k)
        lo = len(r10.filtered(c))
        if d is None:
            seqlen += 1
            sigma += lo
            rows.append([k, lo, None])
            continue
        ld = len(r10.filtered(d))
        sigma += abs(lo - ld)
        if lo != ld:
            seqlen += 1
        kind, msg, defect = r10.strict_compare(c, d)
        if kind is None:
            clean += 1
        rows.append([k, lo, ld, kind])
    return {'funcs': len(orig), 'clean': clean, 'seqlen': seqlen, 'sigma': sigma,
            'rows': rows}


paths = [l.strip() for l in io.open(sys.argv[1], encoding='utf-8') if l.strip()]
out = {}
for p in paths:
    a = measure(p, prod('head', p))
    b = measure(p, prod('cand', p))
    moved = [r for r in zip(a['rows'], b['rows'])
             if (r[0][1], r[0][2], r[0][3]) != (r[1][1], r[1][2], r[1][3] if len(r[1]) > 3 else None)]
    tag = 'STRICT-WORSE' if b['sigma'] > a['sigma'] or b['clean'] < a['clean'] else \
          ('STRICT-BETTER' if b['sigma'] < a['sigma'] or b['clean'] > a['clean'] else 'STRICT-SAME')
    print('%-14s %s' % (tag, p.replace(REPO + '/site-packages/', '')))
    print('    head clean=%d/%d seqlen=%d sigma=%d   cand clean=%d/%d seqlen=%d sigma=%d'
          % (a['clean'], a['funcs'], a['seqlen'], a['sigma'],
             b['clean'], b['funcs'], b['seqlen'], b['sigma']))
    for x, y in moved:
        print('    fn %-40s head %s/%s %s   cand %s/%s %s'
              % (x[0][:40], x[1], x[2], x[3] if len(x) > 3 else '',
                 y[1], y[2], y[3] if len(y) > 3 else ''))
    out[p] = {'head': {k: a[k] for k in ('clean', 'seqlen', 'sigma', 'funcs')},
              'cand': {k: b[k] for k in ('clean', 'seqlen', 'sigma', 'funcs')}}
io.open(ROOT + '/strict_ab_moved.json', 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('TOTAL head sigma=%d clean=%d  cand sigma=%d clean=%d'
      % (sum(v['head']['sigma'] for v in out.values()), sum(v['head']['clean'] for v in out.values()),
         sum(v['cand']['sigma'] for v in out.values()), sum(v['cand']['clean'] for v in out.values())))
