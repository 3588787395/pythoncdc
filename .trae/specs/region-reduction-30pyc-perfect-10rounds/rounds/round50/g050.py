# -*- coding: utf-8 -*-
"""G0 for Round 50: witness battery + real-pyc targets under a candidate core.

usage: python -X utf8 g050.py <core-dir> <out-tag> [wit-dir]
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
WIT = sys.argv[3] if len(sys.argv) > 3 else r'D:\Temp\r50mine\wit50'
BUILD = r'D:/Temp/r50mine/build_' + TAG
sys.stdout.reconfigure(encoding='utf-8')
os.makedirs(BUILD, exist_ok=True)
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('r50g0', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
for k in [k for k in sys.modules if k == 'core' or k.startswith('core.')]:
    del sys.modules[k]
_p = importlib.util.spec_from_file_location('pc50g0', os.path.join(BASE, 'pycdc.py'))
pc = importlib.util.module_from_spec(_p)
_p.loader.exec_module(pc)
print('core = %s' % os.path.dirname(sys.modules['core'].__file__))

TARGETS = [
    'site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc',
    'site-packages/IQCommon/api/klinedata.pyc',
    'site-packages/IQEngine/plugins/plugin_system_log/__init__.pyc',
    'site-packages/IQCommon/strategy/wizard_quant_api.pyc',
    'site-packages/fly/data/quote_handler.pyc',
    'site-packages/fly/data/quotation.pyc',
]
print('---- TARGETS ----')
for rel in TARGETS:
    pyc = os.path.join(REPO, rel.replace('/', os.sep))
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
                bad.append('%s [%s] %s' % (name.split('.')[-1][:28], kind, msg))
        print('%-62s %3d/%-3d %s' % (rel[-62:], n - len(bad), n, ' | '.join(bad)[:170]))
    except Exception as ex:
        print('%-62s ERROR %s' % (rel[-62:], repr(ex)[:120]))

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
        detail = [repr(ex)[:120]]
    rows.append({'w': stem, 'verdict': verdict, 'detail': detail})
    print('%-26s %-9s %s' % (stem, verdict, ' | '.join(detail)[:170]))
io.open(r'D:/Temp/r50mine/g050_%s.json' % TAG, 'w', encoding='utf-8').write(
    json.dumps(rows, ensure_ascii=False, indent=1))
print('battery: MISMATCH=%d MATCH=%d ERROR=%d of %d' % (
    sum(1 for r in rows if r['verdict'] == 'MISMATCH'),
    sum(1 for r in rows if r['verdict'] == 'MATCH'),
    sum(1 for r in rows if r['verdict'] == 'ERROR'), len(rows)))
