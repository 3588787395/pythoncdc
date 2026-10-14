# -*- coding: utf-8 -*-
"""idx_check.py -- verify: in every walk, the dispatching block's iteration index precedes the
first target block's iteration index (so the claim always completes before the reach).

usage: python -X utf8 idx_check.py
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace',
                              line_buffering=True)
M = 'D:/Temp/r110/'
T = set(json.load(open(M + 'logs/census_base.json'))['targets'])
print('n_targets', len(T), sorted(T))
fr = json.load(open(M + 'logs/lines_base.json'))
for s in (304, 313, 319):
    cand = [x for x in fr if x['seq'] == s and x['fn'] == '_process_if_blocks']
    print('seq=%d candidate frames: %d' % (s, len(cand)))
    if not cand:
        continue
    f = cand[0]
    order, disp = [], {}
    for ln, b in f['log']:
        if ln == 26765 or b is None:
            continue
        if b not in order:
            order.append(b)
        if ln == 26869:
            disp[b] = disp.get(b, 0) + 1
    if not order:
        print('  empty order; log len=%d first=%s' % (len(f['log']), f['log'][:3]))
        continue
    di = sorted(order.index(b) for b in disp)
    ti = [i for i, b in enumerate(order) if b in T]
    print('  seq=%d reg=%s n=%d dispatch_blocks=%s idx=%s first_target_idx=%d (@%d) '
          'dispatch_before_all_reaches=%s'
          % (s, f['reg'], len(order), sorted(disp), di, ti[0] if ti else -1,
             order[ti[0]] if ti else -1, bool(di) and max(di) < (ti[0] if ti else 0)))
