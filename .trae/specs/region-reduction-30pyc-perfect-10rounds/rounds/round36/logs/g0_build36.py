# -*- coding: utf-8 -*-
"""Round 36 G0 builder: write the seven synthetic repro sources into the repo repro dir and
compile each to .pyc with an EXPLICIT cfile (CPython otherwise drops them next to the source).

usage: python -X utf8 g0_build36.py
"""
import io
import os
import py_compile
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'D:/Temp/r36gate/r36')
from shapes36 import SHAPES  # noqa: E402

REPO = r'F:\Downloads\pythoncdc-main'
DST = REPO + '/test_repros/round36_for_loop_dropped'
if not os.path.isdir(DST):
    os.makedirs(DST)

for name, src in sorted(SHAPES.items()):
    assert src.endswith('\n') and '\r' not in src, name
    io.open(os.path.join(DST, name + '.py'), 'w', encoding='utf-8', newline='\n').write(src)
    py_compile.compile(os.path.join(DST, name + '.py'),
                       cfile=os.path.join(DST, name + '.pyc'), doraise=True, quiet=2)
    print('wrote %-52s py+pyc (%d lines)' % (name, src.count('\n')))
