# -*- coding: utf-8 -*-
"""Instrument the three `return None` bail paths of _try_build_ternary_kwarg_call.

usage: python -X utf8 dbg50gen.py <src-mirror> <dst-mirror>
"""
import os
import py_compile
import shutil
import sys

SRC, DST = sys.argv[1], sys.argv[2]
sys.stdout.reconfigure(encoding='utf-8')
if os.path.exists(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
P = DST + '/core/cfg/region_ast_generator.py'
raw = open(P, 'rb').read()
bom = raw[:3] == b'\xef\xbb\xbf'
u = raw.decode('utf-8-sig')
nl = '\r\n' if u.count('\r') else '\n'
L = u.replace('\r\n', '\n').replace('\r', '\n').split('\n')

MSG = {
    41519: 'no_func_expr entry=',
    41505: 'preload_kwarg i=',
    41427: 'no_kwnames merge=',
}
EXTRA = {
    41519: 'getattr(getattr(region, "entry", None), "start_offset", None)',
    41505: '(i, kw_names, num_ternaries, '
           'getattr(getattr(region, "entry", None), "start_offset", None))',
    41427: '(getattr(getattr(region, "entry", None), "start_offset", None), '
           'getattr(final_merge, "start_offset", None))',
}
for lineno in sorted(MSG, reverse=True):
    i = lineno - 1
    assert L[i].strip() == 'return None', repr(L[i])
    ind = ' ' * (len(L[i]) - len(L[i].lstrip()))
    args = EXTRA[lineno]
    args = args[len(''):]
    if args.startswith('(') and args.endswith(')'):
        inner = args[1:-1]
        line = ind + 'print("R50GEN %s", %s)' % (MSG[lineno], inner)
    else:
        line = ind + 'print("R50GEN %s", %s)' % (MSG[lineno], args)
    L[i:i] = [line]

out = '\n'.join(L).replace('\n', nl).encode('utf-8')
if bom:
    out = b'\xef\xbb\xbf' + out
open(P, 'wb').write(out)
py_compile.compile(P, doraise=True)
print('instrumented %s (bom=%s)' % (P, bom))
