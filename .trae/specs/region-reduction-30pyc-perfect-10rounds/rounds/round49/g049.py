# -*- coding: utf-8 -*-
"""G0 witness battery for the Round 49 arm/merge-swap family.

usage: python -X utf8 g049.py <core-dir> <out-tag>
"""
import glob
import importlib.util
import io
import json
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
BASE = sys.argv[1]
TAG = sys.argv[2]
WIT = r'D:\Temp\r49mine\wit'
BUILD = r'D:/Temp/r49mine/build_' + TAG
sys.stdout.reconfigure(encoding='utf-8')
os.makedirs(BUILD, exist_ok=True)
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('r10g0', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
for k in [k for k in sys.modules if k == 'core' or k.startswith('core.')]:
    del sys.modules[k]
_p = importlib.util.spec_from_file_location('pc49g0', os.path.join(BASE, 'pycdc.py'))
pc = importlib.util.module_from_spec(_p)
_p.loader.exec_module(pc)
rows = []
for src in sorted(glob.glob(os.path.join(WIT, '*.py'))):
    stem = os.path.basename(src)[:-3]
    pyc = BUILD + '/' + stem + '.pyc'
    prod = BUILD + '/' + stem + '_prod.py'
    pyc2 = BUILD + '/' + stem + '_prod.pyc'
    try:
        py_compile.compile(src, cfile=pyc, doraise=True)
        txt = pc.decompile_pyc(pyc)
        io.open(prod, 'w', encoding='utf-8', newline='\n').write(txt)
        py_compile.compile(prod, cfile=pyc2, doraise=True)
        o = r10._load_map(pyc)
        d = r10._compile_map(prod)
        worst = 'MATCH'
        detail = []
        for name in sorted(o):
            if d.get(name) is None:
                worst = 'MISMATCH'
                detail.append('%s MISSING' % name)
                continue
            kind, msg, isdef = r10.strict_compare(o[name], d[name])
            if isdef:
                if worst == 'MATCH':
                    worst = 'MISMATCH'
                detail.append('%s %s %s' % (name, kind, msg))
        verdict = worst
    except Exception as ex:
        verdict = 'ERROR'
        detail = [repr(ex)[:120]]
    rows.append({'w': stem, 'verdict': verdict, 'detail': detail})
    print('%-30s %-9s %s' % (stem, verdict, ' | '.join(detail)[:150]))
mm = sum(1 for r in rows if r['verdict'] == 'MISMATCH')
print('core=%s tag=%s repros=%d MISMATCH=%d MATCH=%d ERROR=%d' % (
    BASE, TAG, len(rows), mm, len(rows) - mm - sum(1 for r in rows if r['verdict'] == 'ERROR'),
    sum(1 for r in rows if r['verdict'] == 'ERROR')))
io.open(r'D:/Temp/r49mine/g049_%s.json' % TAG, 'w', encoding='utf-8').write(
    json.dumps(rows, ensure_ascii=False, indent=1))
