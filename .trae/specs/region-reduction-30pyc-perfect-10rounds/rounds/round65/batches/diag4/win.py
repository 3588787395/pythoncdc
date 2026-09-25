# -*- coding: utf-8 -*-
"""diag4: print orig vs decomp instructions of one function in an offset window.

usage: python -X utf8 win.py <pyc> <okpy> <func> <lo> <hi>
"""
import dis
import io
import marshal
import sys
import types

sys.path.insert(0, '.')
from align import find_all, instrs, load_pyc  # noqa: E402

pyc, okpy, name, lo, hi = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
oc = find_all(load_pyc(pyc), name)[0]
src = io.open(okpy, encoding='utf-8').read()
dc = find_all(compile(src, okpy, 'exec'), name)[0]
print('=== ORIG %s [%d:%d]' % (name, lo, hi))
for op, arg, off in instrs(oc):
    if lo <= off <= hi:
        print('  %5d %-26s %s' % (off, op, arg))
print('=== DECOMP %s [%d:%d]' % (name, lo, hi))
for op, arg, off in instrs(dc):
    if lo <= off <= hi:
        print('  %5d %-26s %s' % (off, op, arg))
