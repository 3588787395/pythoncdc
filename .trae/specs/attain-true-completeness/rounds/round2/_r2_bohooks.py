#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 debug: trace inner boolop hooks.
usage: _r2_bohooks.py <pyc> <fn>
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

_HOOKS = ['_has_boolop_tail_value_boundary', '_try_build_keeppop_target_grouped',
          '_build_boolop_skipedge_grouped', '_build_grouped_boolop_expression',
          '_try_build_and_inner_or_pattern', '_try_build_chained_compare_in_boolop']


def wrap(mname):
    orig = getattr(RegionASTGenerator, mname)

    def traced(self, *a, **k):
        r = orig(self, *a, **k)
        if r is not None:
            arg0 = a[0] if a else None
            print('  %s(%s) -> %s' % (
                mname,
                getattr(arg0, 'start_offset', ''),
                (r.get('type') if isinstance(r, dict) else r)))
        return r

    return orig, traced


saved = {}
for m in _HOOKS:
    saved[m] = wrap(m)
    setattr(RegionASTGenerator, m, saved[m][1])
print('>> generating')
ast = gen.generate()
for m in _HOOKS:
    setattr(RegionASTGenerator, m, saved[m][0])
print('==== final body ====')
for s in (ast.get('body') or []):
    print('  ', s.get('type'), s.get('value', {}).get('type') if isinstance(s.get('value'), dict) else '')
