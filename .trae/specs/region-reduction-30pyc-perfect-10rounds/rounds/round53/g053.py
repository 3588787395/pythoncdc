# -*- coding: utf-8 -*-
"""G0 for Round 53: witness battery + real-pyc targets under a candidate core.

usage: python -X utf8 g052.py <core-dir> <out-tag> [wit-dir] [targets-file]

targets-file: newline-separated paths relative to the repo root; defaults to
D:/Temp/r53gate/targets53.txt.  The battery dir is compiled+strict-checked with the
same core.  Defect messages are printed IN FULL (Round 51 learned that truncating them
to 170 chars can hide a real fix).
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
WIT = sys.argv[3] if len(sys.argv) > 3 else r'D:\Temp\r52mine\wit52'
TGT = sys.argv[4] if len(sys.argv) > 4 else r'D:\Temp\r52gate\targets53.txt'
BUILD = r'D:/Temp/r53gate/build_' + TAG
sys.stdout.reconfigure(encoding='utf-8')
os.makedirs(BUILD, exist_ok=True)
sys.path.insert(0, BASE)
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('r53sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
for k in [k for k in sys.modules if k == 'core' or k.startswith('core.')]:
    del sys.modules[k]
_p = importlib.util.spec_from_file_location('pc53', os.path.join(BASE, 'pycdc.py'))
pc = importlib.util.module_from_spec(_p)
_p.loader.exec_module(pc)
COREDIR = os.path.dirname(sys.modules['core'].__file__)
print('core = %s' % COREDIR)
assert os.path.normcase(COREDIR).startswith(os.path.normcase(BASE)), \
    'BROKEN INSTRUMENT: core resolved outside BASE'

TARGETS = [l.strip() for l in io.open(TGT, encoding='utf-8') if l.strip()]
print('---- TARGETS (%d) ----' % len(TARGETS))
rows_t = []
for rel in TARGETS:
    pyc = os.path.join(REPO, 'site-packages', rel.replace('/', os.sep))
    if not os.path.exists(pyc):
        print('MISSING %s' % rel)
        continue
    try:
        txt = pc.decompile_pyc(pyc)
        prod = BUILD + '/' + rel.replace('/', '_')[:-4] + '.py'
        io.open(prod, 'w', encoding='utf-8', newline='\n').write(txt)
        o = r10._load_map(pyc)
        d = r10._compile_map(prod)
        bad = []
        n = 0
        for name in sorted(set(o) & set(d)):
            n += 1
            kind, msg, isdef = r10.strict_compare(o[name], d[name])
            if isdef:
                bad.append('%s [%s] %s' % (name, kind, msg))
        print('%-62s %3d/%-3d' % (rel[-62:], n - len(bad), n))
        for b in bad:
            print('    ' + b)
        rows_t.append({'path': rel, 'strict_matched': n - len(bad), 'total': n,
                       'defects': bad})
    except Exception as ex:
        print('%-62s ERROR %s' % (rel[-62:], repr(ex)[:200]))
        rows_t.append({'path': rel, 'error': repr(ex)[:200]})

print('---- BATTERY %s ----' % WIT)
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
        detail = [repr(ex)[:200]]
    rows.append({'w': stem, 'verdict': verdict, 'detail': detail})
    print('%-26s %-9s %s' % (stem, verdict, ' | '.join(detail)))
io.open(r'D:/Temp/r53gate/g053_%s.json' % TAG, 'w', encoding='utf-8').write(
    json.dumps({'targets': rows_t, 'battery': rows}, ensure_ascii=False, indent=1))
print('battery: MISMATCH=%d MATCH=%d ERROR=%d of %d' % (
    sum(1 for r in rows if r['verdict'] == 'MISMATCH'),
    sum(1 for r in rows if r['verdict'] == 'MATCH'),
    sum(1 for r in rows if r['verdict'] == 'ERROR'), len(rows)))
