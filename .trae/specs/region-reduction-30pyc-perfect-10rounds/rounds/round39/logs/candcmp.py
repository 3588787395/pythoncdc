# -*- coding: utf-8 -*-
"""Round 39 line A, step 5: which SOURCE shape recompiles byte-identically to the
witness's ORIGINAL instruction sequence?

usage: python -X utf8 candcmp.py <orig-src.py> <orig-fn> <cand1.py> <cand1-fn> [<cand2.py> <cand2-fn> ...]
"""
import dis
import importlib.util
import io
import os
import py_compile
import sys

pos = [x for x in sys.argv[1:]]
REPO = r'F:\Downloads\pythoncdc-main'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
os.chdir(HERE)
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)


def fn_map(src, tag):
    pyc = os.path.join(HERE, 'candcmp_%s.pyc' % tag)
    py_compile.compile(os.path.abspath(src), cfile=pyc, doraise=True, quiet=2)
    m = r10._load_map(pyc)
    return m, pyc


def show(name, code):
    print('--- %s (%d filtered) ---' % (name, len(r10.filtered(code))))
    n = 0
    for i in dis.get_instructions(code):
        if i.opname in r10.NOISE:
            continue
        n += 1
        j = ' -> %s' % i.argval if r10._is_jump(i.opname) else ''
        print('  %3d @%-4d %-26s %-22r%s' % (n, i.offset, i.opname,
                                             '<code>' if hasattr(i.argval, 'co_code') else i.argrepr, j))


orig, _ = fn_map(pos[0], 'orig')
ofn = pos[1]
okey = [k for k in orig if k == ofn or k.endswith('.' + ofn)]
assert len(okey) == 1, okey
okey = okey[0]
show('ORIGINAL %s' % okey, orig[okey])

pairs = pos[2:]
for i in range(0, len(pairs), 2):
    src, fn = pairs[i], pairs[i + 1]
    m, _ = fn_map(src, 'c%d' % (i // 2))
    key = [k for k in m if k == fn or k.endswith('.' + fn)]
    assert len(key) == 1, (src, fn, list(m))
    key = key[0]
    print('\n=== candidate %s (%s) : strict %s' % (fn, os.path.basename(src),
                                                   r10.strict_compare(orig[okey], m[key])))
    show('CAND %s' % key, m[key])
