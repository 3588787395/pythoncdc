# -*- coding: utf-8 -*-
"""R5: extract probe command lists from prior stamps (neg/neg3/r4prot/b122/neigh)."""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STAMPS = ['rec1_probes_r5fix4neg.json', 'rec1_probes_r5fix4neg3.json',
          'rec1_probes_r5fix4r4prot.json', 'rec1_probes_r5fix4b122.json',
          'rec1_probes_r5fix4neigh.json']

out = io.open(os.path.join(HERE, '_r5_battery_cmds.txt'), 'w', encoding='utf-8')
for st in STAMPS:
    p = os.path.join(HERE, st)
    if not os.path.exists(p):
        out.write('%s MISSING\n' % st)
        continue
    data = json.load(io.open(p, encoding='utf-8'))
    probes = data.get('probes', []) if isinstance(data, dict) else data
    out.write('=== %s ===\n' % st)
    for pr in probes:
        name = pr.get('name')
        src = pr.get('pyc_src_rel') or pr.get('pyc') or ''
        ok = pr.get('units_success')
        tot = pr.get('units_total')
        errs = '; '.join(pr.get('failures', []) or [])[:80]
        out.write('%s=%s units=%s/%s %s\n' % (name, src, ok, tot, errs))
out.close()
print('done')
