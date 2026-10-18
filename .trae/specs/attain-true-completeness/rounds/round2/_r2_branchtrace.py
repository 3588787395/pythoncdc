#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: line-trace _generate_boolop_impl branch for one function."""
import ast
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

pyc = sys.argv[1]
name = sys.argv[2]
lo = int(sys.argv[3]) if len(sys.argv) > 3 else 45080
hi = int(sys.argv[4]) if len(sys.argv) > 4 else 47000

data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


targets = []
find_code(code, name, targets)
co = targets[-1]

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)

RAG = os.path.join(ROOT, 'core', 'cfg', 'region_ast_generator.py')
lines_seq = []


def tracer(frame, event, arg):
    if event == 'line':
        fn = frame.f_code.co_filename
        if os.path.basename(fn) == 'region_ast_generator.py':
            ln = frame.f_lineno
            if lo <= ln <= hi:
                lines_seq.append(ln)
    return tracer


sys.settrace(tracer)
try:
    out = gen.generate()
finally:
    sys.settrace(None)

# collapse consecutive repeats
prev = None
collapsed = []
for ln in lines_seq:
    if ln != prev:
        collapsed.append(ln)
        prev = ln
print('lines:', collapsed[:400])
try:
    print(ast.unparse(out))
except Exception:
    print(repr(out)[:2000])
