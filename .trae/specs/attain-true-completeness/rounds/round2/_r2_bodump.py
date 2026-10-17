#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: dump BoolOpRegion op_chain + _build_boolop_expression for listed fns."""
import io
import json
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
names = sys.argv[2:]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


for name in names:
    targets = []
    find_code(code, name, targets)
    co = targets[-1]
    cfg = build_cfg(co)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    regs = gen.region_analyzer.analyze()
    print('==== %s ====' % name)
    for r in regs:
        if isinstance(r, BoolOpRegion):
            print('BOOLOP entry=@%d merge=@%d vt=%r ctx=%r' % (
                r.entry.start_offset,
                r.merge_block.start_offset if r.merge_block else -1,
                getattr(r, 'value_target', None),
                getattr(r, 'merge_context', None)))
            print('   op_chain=%s' % [(b.start_offset, o) for b, o in r.op_chain])
            try:
                expr = gen._build_boolop_expression(r)
                print('   expr=%s' % json.dumps(expr, default=str)[:400])
            except Exception as exc:
                print('   expr EXC %r' % exc)
