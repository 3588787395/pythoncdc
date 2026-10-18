#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 debug: dump BoolOpRegion details + trace _generate_boolop.
usage: _r2_bodump2.py <pyc> <fn>
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
from core.cfg.region_analyzer import BoolOpRegion

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

_orig = RegionASTGenerator._generate_boolop


def traced(self, region, skip_store_targets=None):
    print('>> _generate_boolop entry=@%s' % region.entry.start_offset)
    r = _orig(self, region, skip_store_targets)
    print('<< _generate_boolop -> %s' % (
        ('list[%d]' % len(r) if isinstance(r, list) else
         (r.get('type') if isinstance(r, dict) else r))))
    return r


RegionASTGenerator._generate_boolop = traced
ast = gen.generate()
RegionASTGenerator._generate_boolop = _orig
for r in gen.region_analyzer.regions:
    if isinstance(r, BoolOpRegion):
        print('BoolOpRegion entry=@%s merge=@%s blocks=%s' % (
            r.entry.start_offset, r.merge_block.start_offset if r.merge_block else None,
            [b.start_offset for b in r.blocks]))
        print('  op_chain=%s' % [(b.start_offset, op) for b, op in (r.op_chain or [])])
        print('  value_target=%r merge_context=%r' % (
            getattr(r, 'value_target', None), getattr(r, 'merge_context', None)))
        print('  parent=%s' % (type(r.parent).__name__ if r.parent else None))
print('==== final body ====')
for s in (ast.get('body') or []):
    print('  ', s.get('type'))
