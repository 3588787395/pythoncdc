# -*- coding: utf-8 -*-
"""Battery-only strict check of D:/Temp/r51mine/wit52 under a given core.

usage: python -X utf8 witrun51.py <core-dir> <out-tag>
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
WIT = r'D:\Temp\r52mine\wit52'
BUILD = r'D:/Temp/r52gate/witbuild_' + TAG
sys.stdout.reconfigure(encoding='utf-8')
os.makedirs(BUILD, exist_ok=True)
sys.path.insert(0, BASE)
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('r51w', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
for k in [k for k in sys.modules if k == 'core' or k.startswith('core.')]:
    del sys.modules[k]
_p = importlib.util.spec_from_file_location('pc51w', os.path.join(BASE, 'pycdc.py'))
pc = importlib.util.module_from_spec(_p)
_p.loader.exec_module(pc)
COREDIR = os.path.dirname(sys.modules['core'].__file__)
print('core = %s' % COREDIR)
assert os.path.normcase(COREDIR).startswith(os.path.normcase(BASE)), \
    'BROKEN INSTRUMENT: core resolved outside BASE'

rows = []
for src in sorted(glob.glob(os.path.join(WIT, '*.py'))):
    stem = os.path.basename(src)[:-3]
    pyc = BUILD + '/' + stem + '.pyc'
    prod = BUILD + '/' + stem + '_prod.py'
    try:
        py_compile.compile(src, cfile=pyc, doraise=True)
        txt = pc.decompile_pyc(pyc)
        io.open(prod, 'w', encoding='utf-8', newline='\n').write(txt)
        o = r10._load_map(pyc)
        d = r10._compile_map(prod)
        verdict = 'MATCH'
        detail = []
        for name in sorted(o):
            if d.get(name) is None:
                verdict = 'MISMATCH'
                detail.append('%s MISSING' % name)
                continue
            kind, msg, isdef = r10.strict_compare(o[name], d[name])
            if isdef:
                verdict = 'MISMATCH'
                detail.append('%s %s %s' % (name, kind, msg))
    except Exception as ex:
        verdict = 'ERROR'
        detail = [repr(ex)[:160]]
    rows.append({'w': stem, 'verdict': verdict, 'detail': detail})
    print('%-26s %-9s %s' % (stem, verdict, ' | '.join(detail)[:150]))
io.open(r'D:/Temp/r52gate/wit52_%s.json' % TAG, 'w', encoding='utf-8').write(
    json.dumps(rows, ensure_ascii=False, indent=1))
print('battery %s: MISMATCH=%d MATCH=%d ERROR=%d of %d' % (
    TAG, sum(1 for r in rows if r['verdict'] == 'MISMATCH'),
    sum(1 for r in rows if r['verdict'] == 'MATCH'),
    sum(1 for r in rows if r['verdict'] == 'ERROR'), len(rows)))
