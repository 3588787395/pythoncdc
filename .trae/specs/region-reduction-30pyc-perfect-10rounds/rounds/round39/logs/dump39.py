# -*- coding: utf-8 -*-
"""Round 39 line A, step 1: dump ORIGINAL vs PRODUCT instruction sequences for one synthetic
function that reproduces the 'elif chain tail continue' shape, on the LANDED bytes.

usage: python -X utf8 dump39.py <src.py> <func-name> [--core=<mirror-root>]
"""
import dis
import importlib.util
import io
import os
import py_compile
import sys

kw = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
pos = [x for x in sys.argv[1:] if not x.startswith('--')]
SRC_ARG = os.path.abspath(pos[0]) if pos else None
ROOT = os.path.abspath(kw.get('core', r'F:\Downloads\pythoncdc-main'))
REPO = r'F:\Downloads\pythoncdc-main'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
if ROOT != REPO:
    sys.path.append(REPO)
os.chdir(ROOT)
sys.stdout.reconfigure(encoding='utf-8')

_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
import pycdc  # noqa: E402

src = SRC_ARG
tail = pos[1]
work = os.path.join(HERE, 'dump39_work')
os.makedirs(work, exist_ok=True)
orig_pyc = os.path.join(work, 'orig.pyc')
py_compile.compile(src, cfile=orig_pyc, doraise=True, quiet=2)

prod = pycdc.decompile_pyc(orig_pyc)
prod_py = os.path.join(work, 'prod.py')
io.open(prod_py, 'w', encoding='utf-8').write(prod)
prod_pyc = os.path.join(work, 'prod.pyc')
py_compile.compile(prod_py, cfile=prod_pyc, doraise=True, quiet=2)

o_map, d_map = r10._load_map(orig_pyc), r10._compile_map(prod_py)
names = [k for k in o_map if k == tail or k.endswith('.' + tail)]
assert len(names) == 1, names
name = names[0]


def show(tag, code):
    print('--- %s %s (%d filtered instr) ---' % (tag, name, len(r10.filtered(code))))
    n = 0
    for i in dis.get_instructions(code):
        if i.opname in r10.NOISE:
            continue
        n += 1
        j = ' -> %s' % i.argval if r10._is_jump(i.opname) else ''
        print('  %3d @%-4d %-26s %-24r%s' % (n, i.offset, i.opname,
                                             '<code>' if hasattr(i.argval, 'co_code') else i.argrepr, j))


show('ORIGINAL', o_map[name])
show('PRODUCT', d_map[name])
print('strict:', r10.strict_compare(o_map[name], d_map[name]))
print('--- product source ---')
print('\n'.join('%3d| %s' % (i + 1, l) for i, l in enumerate(prod.splitlines())))
