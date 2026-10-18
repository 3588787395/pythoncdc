#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 debug: trace _build_boolop_expression result for a function.
usage: _r2_botrace.py <pyc> <fn>
"""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

pyc = sys.argv[1]
name = sys.argv[2]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])
targets = []


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)

_orig = RegionASTGenerator._build_boolop_expression


def traced(self, region, skip_elif_blocks=True):
    r = _orig(self, region, skip_elif_blocks)
    print('>> _build_boolop_expression entry=@%s -> %r' % (
        region.entry.start_offset, r))
    return r


RegionASTGenerator._build_boolop_expression = traced
ast = gen.generate()
RegionASTGenerator._build_boolop_expression = _orig
print('==== final body ====')
for s in (ast.get('body') or []):
    print('  ', s.get('type'), s.get('value', {}).get('type') if isinstance(s.get('value'), dict) else '')
