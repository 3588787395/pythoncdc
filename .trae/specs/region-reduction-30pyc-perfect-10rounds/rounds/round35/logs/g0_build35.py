# -*- coding: utf-8 -*-
"""Round 35 G0 builder: write the synthetic repro sources, compile each to .pyc with an
EXPLICIT cfile (CPython otherwise drops them next to the source).

usage: python -X utf8 g0_build35.py
"""
import io
import os
import py_compile
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'D:/Temp/r35gate/r35')
from shapes35 import SHAPES  # noqa: E402

REPO = r'F:\Downloads\pythoncdc-main'
DST = REPO + '/test_repros/round35_epilogue_duplicate_return'
if not os.path.isdir(DST):
    os.makedirs(DST)

for name, sh in sorted(SHAPES.items()):
    src = sh['src']
    assert src.endswith('\n') and '\r' not in src, name
    io.open(os.path.join(DST, name + '.py'), 'w', encoding='utf-8', newline='\n').write(src)
    py_compile.compile(os.path.join(DST, name + '.py'),
                       cfile=os.path.join(DST, name + '.pyc'), doraise=True, quiet=2)
    print('wrote %-46s py+pyc (%d lines, alt differs by %d lines)'
          % (name, src.count('\n'), sh['alt'].count('\n') - src.count('\n')))
