# -*- coding: utf-8 -*-
"""Decompile one pyc with a mirror core and dump selected functions.

usage: python -X utf8 prod50m.py <mirror-dir> <tag> <pyc> <func-name> [func-name...]
"""
import ast
import importlib.util
import io
import os
import sys

MIRROR, TAG = sys.argv[1], sys.argv[2]
PYC = sys.argv[3]
NAMES = sys.argv[4:]
REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:\Temp\r50mine\prod_%s_%s.py' % (TAG, PYC.replace('\\', '/').split('/')[-1][:-4])
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, REPO)
for k in [k for k in sys.modules if k == 'core' or k.startswith('core.')]:
    del sys.modules[k]
sys.path.insert(0, MIRROR)
_s = importlib.util.spec_from_file_location('pc50m', os.path.join(MIRROR, 'pycdc.py'))
pc = importlib.util.module_from_spec(_s)
_s.loader.exec_module(pc)
import core
print('core =', os.path.dirname(core.__file__))
txt = pc.decompile_pyc(PYC)
io.open(OUT, 'w', encoding='utf-8', newline='\n').write(txt)
print('product: %s (%d bytes)' % (OUT, len(txt.encode('utf-8'))))
tree = ast.parse(txt)
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in NAMES:
        seg = ast.get_source_segment(txt, node)
        print('===== %s (%d lines) =====' % (node.name, seg.count('\n') + 1))
        print(seg)
