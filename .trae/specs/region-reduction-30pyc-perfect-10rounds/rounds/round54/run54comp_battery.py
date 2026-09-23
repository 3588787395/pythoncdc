# -*- coding: utf-8 -*-
"""Run the Round 55 witness battery with an arbitrary core.

usage: python -X utf8 run55b.py <core-dir> <tag>
"""
import glob
import importlib.util
import io
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
HERE = r'D:/Temp/r54mine55'
BASE = os.path.abspath(sys.argv[1])
TAG = sys.argv[2]
PROD = HERE + '/prod_' + TAG
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('r55sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
for k in [k for k in sys.modules if k == 'core' or k.startswith('core.')]:
    del sys.modules[k]
_p = importlib.util.spec_from_file_location('pc55b', os.path.join(BASE, 'pycdc.py'))
pc = importlib.util.module_from_spec(_p)
sys.path.insert(0, BASE)
_p.loader.exec_module(pc)
COREDIR = os.path.join(os.path.dirname(pc.__file__), 'core')
assert os.path.normcase(COREDIR).startswith(os.path.normcase(BASE)), 'core resolved outside BASE'
print('core =', COREDIR)
os.makedirs(PROD, exist_ok=True)
n_bad = n_ok = 0
for src in sorted(glob.glob(HERE + '/w55_*.py')):
    pyc = src[:-3] + '.pyc'
    py_compile.compile(src, cfile=pyc, doraise=True)
    txt = pc.decompile_pyc(os.path.abspath(pyc))
    out = os.path.join(PROD, os.path.basename(src)[:-3] + 'OK.py')
    io.open(out, 'w', encoding='utf-8', newline='').write(txt)
    o = r10._load_map(os.path.abspath(pyc))
    d = r10._compile_map(out)
    bad = []
    for n in sorted(set(o) & set(d)):
        kind, msg, is_def = r10.strict_compare(o[n], d[n])
        if is_def:
            bad.append('%s %s %s' % (n, kind, msg))
    n_bad += bool(bad)
    n_ok += not bool(bad)
    print('%-42s %s' % (os.path.basename(src), 'MATCH' if not bad else 'MISMATCH'))
    for b in bad:
        print('      ' + b[:118])
print('battery[%s]: MISMATCH=%d MATCH=%d of %d' % (TAG, n_bad, n_ok, n_bad + n_ok))
