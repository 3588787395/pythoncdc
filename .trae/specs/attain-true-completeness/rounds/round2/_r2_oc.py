#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: dump BoolOpRegion op_chain with each member block's last instruction."""
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
from core.cfg.region_analyzer import BoolOpRegion, TernaryRegion

pyc = sys.argv[1]
name = sys.argv[2]
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
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
regs = gen.region_analyzer.analyze()

for r in regs:
    if isinstance(r, BoolOpRegion):
        print('BoolOpRegion entry=@%s merge=@%s is_cond_ctx=%s' % (
            r.entry.start_offset,
            getattr(getattr(r, 'merge_block', None), 'start_offset', None),
            getattr(r, 'is_cond_ctx', None)))
        for b, op in (r.op_chain or []):
            li = b.get_last_instruction()
            print('   chain (%s, %s)  block@%s last=%s arg=%s' % (
                getattr(b, 'start_offset', None), op, getattr(b, 'start_offset', None),
                getattr(li, 'opname', None), getattr(li, 'arg', None)))
    elif isinstance(r, TernaryRegion):
        print('TernaryRegion entry=@%s cond=@%s tv=@%s fv=@%s merge=@%s mt=%s vt=%s mc=%s' % (
            r.entry.start_offset,
            getattr(getattr(r, 'condition_block', None), 'start_offset', None),
            getattr(getattr(r, 'true_value_block', None), 'start_offset', None),
            getattr(getattr(r, 'false_value_block', None), 'start_offset', None),
            getattr(getattr(r, 'merge_block', None), 'start_offset', None),
            getattr(r, 'merge_context', None), getattr(r, 'value_target', None),
            getattr(r, 'merge_context', None)))
