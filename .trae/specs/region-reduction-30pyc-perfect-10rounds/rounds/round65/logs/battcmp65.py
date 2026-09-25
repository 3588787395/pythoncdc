# -*- coding: utf-8 -*-
"""Compare the two battery dumps (pre-round `r63` column vs `landed` column)."""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
GATE = r'D:/Temp/opencode/r65gate'


def load(arm):
    d = {}
    for l in io.open('%s/dump/repro64_%s.jsonl' % (GATE, arm), encoding='utf-8'):
        if l.strip():
            r = json.loads(l)
            d[r['path'].replace('\\', '/')] = r
    return d


a, b = load('r63'), load('landed')
ta = tb = ca = cb = n = 0
for p in sorted(set(a) | set(b)):
    ra, rb = a.get(p), b.get(p)
    if not ra or not rb:
        print('MISSING-COLUMN %s  r63=%s landed=%s' % (p, bool(ra), bool(rb)))
        continue
    n += 1
    ma, mb = int(ra['matched_functions']), int(rb['matched_functions'])
    ta += ma
    tb += mb
    ca += ma == int(ra['total_functions'])
    cb += mb == int(rb['total_functions'])
    tag = '' if mb >= ma else '   <<< WORSE'
    if ma != mb or tag:
        print('%-58s r63 %2d/%-2d -> landed %2d/%-2d%s'
              % (p.split('test_repros/')[-1], ma, int(ra['total_functions']), mb,
                 int(rb['total_functions']), tag))
print('repros %d   r63 %d matched / %d clean  ->  landed %d matched / %d clean' % (n, ta, ca, tb, cb))
