# -*- coding: utf-8 -*-
"""Generic witness runner: compile *.py in a dir, decompile with a chosen core, strict-check.

usage: python -X utf8 runw.py <core-dir> <witness-dir> <tag>
"""
import glob
import importlib.util
import io
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
BASE = os.path.abspath(sys.argv[1])
WIT = os.path.abspath(sys.argv[2])
TAG = sys.argv[3]
PROD = r'D:/Temp/r55diag/prod_' + TAG
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('rwsc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
for k in [k for k in sys.modules if k == 'core' or k.startswith('core.')]:
    del sys.modules[k]
sys.path.insert(0, BASE)
_p = importlib.util.spec_from_file_location('pcw', os.path.join(BASE, 'pycdc.py'))
pc = importlib.util.module_from_spec(_p)
_p.loader.exec_module(pc)
assert os.path.normcase(os.path.join(os.path.dirname(pc.__file__), 'core')).startswith(
    os.path.normcase(BASE)), 'core resolved outside BASE'
os.makedirs(PROD, exist_ok=True)

bad_n = ok_n = 0
for src in sorted(glob.glob(WIT + '/*.py')):
    pyc = src[:-3] + '.pyc'
    try:
        py_compile.compile(src, cfile=pyc, doraise=True)
    except Exception as e:
        print('%-46s ERROR %s' % (os.path.basename(src), str(e)[:60]))
        continue
    txt = pc.decompile_pyc(os.path.abspath(pyc))
    out = os.path.join(PROD, os.path.basename(src)[:-3] + 'OK.py')
    io.open(out, 'w', encoding='utf-8', newline='').write(txt)
    o = r10._load_map(os.path.abspath(pyc))
    d = r10._compile_map(out)
    bad = ['%s %s %s' % (n, k, m) for n in sorted(set(o) & set(d))
           for k, m, isdef in [r10.strict_compare(o[n], d[n])] if isdef]
    bad_n += bool(bad)
    ok_n += not bad
    print('%-46s %s' % (os.path.basename(src), 'MATCH' if not bad else 'MISMATCH'))
    for b in bad:
        print('      ' + b[:112])
print('battery[%s]: MISMATCH=%d MATCH=%d of %d' % (TAG, bad_n, ok_n, bad_n + ok_n))
