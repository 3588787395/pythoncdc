# -*- coding: utf-8 -*-
"""Round 54 target acquisition: strict defect census over every partial pyc.

Uses ONLY the products already on disk (the strict ruler recompiles the emitted
source), so no core/ is executed and no arm is involved. Classification is by the
*shape* of the defect as reported by the ruler, which is what decides which round
a function belongs to.

usage: python -X utf8 census54_all.py <shard-index> <nshards>
"""
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:/Temp/r54gate/census54'
sys.stdout.reconfigure(encoding='utf-8')
os.makedirs(OUT, exist_ok=True)
_sh = int(sys.argv[1]) if len(sys.argv) > 1 else 0
_ns = int(sys.argv[2]) if len(sys.argv) > 2 else 1
_s = importlib.util.spec_from_file_location('r54sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

idx = json.load(io.open(REPO + '/pyc_index.json', encoding='utf-8'))
part = [e['path'] for e in idx if e['matched_functions'] < e['function_count']]
part.sort()
mine = [p for i, p in enumerate(part) if i % _ns == _sh]
rows = []
for p in mine:
    pyc = os.path.abspath(p.replace('/', os.sep))
    prod = pyc[:-4] + 'OK.py'
    if not os.path.exists(prod):
        rows.append({'pyc': p, 'error': 'no product'})
        continue
    o = r10._load_map(pyc)
    d = r10._compile_map(prod)
    defs = []
    for n in sorted(set(o) & set(d)):
        kind, msg, bad = r10.strict_compare(o[n], d[n])
        if bad:
            defs.append('%s|%s' % (kind, msg))
        elif kind is None:
            pass
    miss = sorted(set(o) - set(d))
    rows.append({'pyc': p.split('site-packages/')[-1], 'strict_ok': len(set(o) & set(d)) - len(defs),
                 'strict_all': len(set(o) & set(d)), 'official': '%d/%d' % (
                     e2 for e2 in []) if False else '', 'missing': miss, 'defects': defs})

io.open(os.path.join(OUT, 'shard_%d.json' % _sh), 'w', encoding='utf-8').write(
    json.dumps(rows, ensure_ascii=False, indent=1))
print('shard %d/%d files=%d' % (_sh, _ns, len(mine)))
for r in rows:
    print('%-56s %3d/%-3d defects=%d' % (r['pyc'][-56:], r.get('strict_ok', -1),
                                         r.get('strict_all', -1), len(r.get('defects', []))))
