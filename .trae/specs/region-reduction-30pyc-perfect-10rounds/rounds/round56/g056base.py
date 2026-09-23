# -*- coding: utf-8 -*-
"""G0 baseline for Round 54: per-target strict table from the LANDED products on disk.

No core execution: the strict ruler recompiles the already-generated *OK.py and
compares per code object, so this is a pure "before" snapshot for the arm run.
usage: python -X utf8 g054base.py > g054base.log 2>&1
"""
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r54sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

targets = [l.strip() for l in io.open(r'D:/Temp/r54gate/targets54.txt', encoding='utf-8')
           if l.strip()]
tot_ok = tot_all = 0
rows = []
for p in targets:
    pyc = os.path.abspath(p.replace('/', os.sep))
    prod = pyc[:-4] + 'OK.py'
    o = r10._load_map(pyc)
    d = r10._compile_map(prod)
    names = sorted(set(o) & set(d))
    bad = []
    for n in names:
        kind, msg, is_def = r10.strict_compare(o[n], d[n])
        if is_def:
            bad.append('%s %s %s' % (n, kind, msg))
    tot_ok += len(names) - len(bad)
    tot_all += len(names)
    rows.append({'pyc': os.path.basename(pyc), 'ok': len(names) - len(bad), 'all': len(names),
                 'defects': bad})
    print('%-46s strict %3d/%3d  defects=%d' % (p.split('site-packages/')[-1][:46],
                                                len(names) - len(bad), len(names), len(bad)))
print('TOTAL strict %d/%d' % (tot_ok, tot_all))
io.open(r'D:/Temp/r54gate/g054base.json', 'w', encoding='utf-8').write(
    json.dumps({'total_ok': tot_ok, 'total_all': tot_all, 'rows': rows},
              ensure_ascii=False, indent=1))
