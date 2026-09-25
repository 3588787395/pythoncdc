# -*- coding: utf-8 -*-
"""Print the two-column battery table from the harness dumps (post-65 rename helper).

  python -X utf8 battable67.py <arm_a> <arm_b>

closeout67's own printer can be cut off by the 300 s rule when both columns still have work
left; this reads the persisted dumps instead, so the gate reading is never quoted from a
half-run.
"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
a, b = sys.argv[1], sys.argv[2]
rows = {}
for arm in (a, b):
    d = {}
    for l in io.open('dump/repro65_%s.jsonl' % arm, encoding='utf-8'):
        if l.strip():
            r = json.loads(l)
            d[r['path'].replace(chr(92), '/')] = r
    rows[arm] = d
paths = sorted(set(rows[a]) | set(rows[b]))
tot = {a: [0, 0], b: [0, 0]}
worse = same = better = 0
for p in paths:
    cells = []
    for arm in (a, b):
        r = rows[arm].get(p)
        if r is None:
            cells.append('%-22s' % 'NO-RECORD')
            continue
        bad = len(r['mism'] or [])
        delta = sum((m[2] or 0) - (m[1] or 0) for m in (r['mism'] or []))
        tot[arm][0] += r['matched_functions']
        tot[arm][1] += r['total_functions']
        cells.append('%-22s' % ('%d/%d bad=%d d=%+d' % (r['matched_functions'],
                                                        r['total_functions'], bad, delta)))
        if arm == b and p in rows[a]:
            lb = len(rows[a][p]['mism'] or [])
            if bad < lb:
                better += 1
            elif bad > lb:
                worse += 1
            else:
                same += 1
    label = p.split('test_repros/')[-1] if 'test_repros/' in p else p.split('/')[-1]
    print('%-58s %s' % (label, '  '.join(cells)))
print('items=%d  matched %s=%d/%d  %s=%d/%d' % (len(paths), a, tot[a][0], tot[a][1], b, tot[b][0], tot[b][1]))
print('defect-functions %s=%d %s=%d | fewer=%d equal=%d WORSE=%d'
      % (a, sum(len(rows[a][p]['mism'] or []) for p in paths if p in rows[a]),
         b, sum(len(rows[b][p]['mism'] or []) for p in paths if p in rows[b]), better, same, worse))
errs = [(arm, p, rows[arm][p].get('error')) for arm in (a, b) for p in rows[arm]
        if rows[arm][p].get('error')]
print('errors=%d %s' % (len(errs), errs[:3]))
