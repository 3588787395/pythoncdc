# -*- coding: utf-8 -*-
"""Round 53 diagnosis runner: compile a witness .py with the system interpreter, then
decompile its pyc through an instrumented mirror core so the [R53 ...] traces show the
operand-chain decisions.

usage: python -X utf8 diag53.py <arm-dir-name|landed> <witness.py> [decomp-out-file]
  e.g. python -X utf8 diag53.py diag53 D:/Temp/r53mine/wit53b/r53_13_or_and_return.py
"""
import importlib.util as iu
import io
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r53gate'
sys.stdout.reconfigure(encoding='utf-8')

spec = iu.spec_from_file_location('r53h', ROOT + '/r53a.py')
h = iu.module_from_spec(spec)
spec.loader.exec_module(h)

arm = sys.argv[1]
src = os.path.abspath(sys.argv[2]).replace('\\', '/')
name = os.path.splitext(os.path.basename(src))[0]
bd = ROOT + '/pyc53'
os.makedirs(bd, exist_ok=True)
pyc = bd + '/%s.pyc' % name
py_compile.compile(src, cfile=pyc, doraise=True)

pycdc = h._load_arm(arm)
text = pycdc.decompile_pyc(pyc)
if len(sys.argv) > 3:
    io.open(sys.argv[3], 'w', encoding='utf-8').write(text)
print('---- product ----')
print(text)
