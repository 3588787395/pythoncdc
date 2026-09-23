# -*- coding: utf-8 -*-
"""How much of the remaining defect corpus is comprehension-shaped?

Scans every partial pyc's defective code objects and keeps those whose qualified
name contains a comprehension marker (<listcomp>, <dictcomp>, <setcomp>, <genexpr>).
Reads only products already on disk; the strict ruler recompiles them.
usage: python -X utf8 comp54.py <shard> <nshards>
"""
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')
_sh = int(sys.argv[1]) if len(sys.argv) > 1 else 0
_ns = int(sys.argv[2]) if len(sys.argv) > 2 else 1
_s = importlib.util.spec_from_file_location('r54c2', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
idx = json.load(io.open(REPO + '/pyc_index.json', encoding='utf-8'))
part = sorted(e['path'] for e in idx if e['matched_functions'] < e['function_count'])
mine = [p for i, p in enumerate(part) if i % _ns == _sh]
hits = []
n_def = 0
for p in mine:
    pyc = os.path.abspath(p.replace('/', os.sep))
    prod = pyc[:-4] + 'OK.py'
    o = r10._load_map(pyc)
    d = r10._compile_map(prod)
    for n in sorted(set(o) & set(d)):
        kind, msg, bad = r10.strict_compare(o[n], d[n])
        if not bad:
            continue
        n_def += 1
        if any(t in n for t in ('<listcomp>', '<dictcomp>', '<setcomp>', '<genexpr>')):
            hits.append('%s :: %s | %s %s' % (p.split('site-packages/')[-1], n, kind, msg))
print('shard %d: files=%d strict defects=%d comprehension-shaped=%d' % (_sh, len(mine), n_def, len(hits)))
for h in hits:
    print('   ' + h[:150])
