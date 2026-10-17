#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: 生成路径追踪 v2（fresh，单次 generate；不改树）。"""
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
from core.cfg.region_analyzer import (
    BoolOpRegion, TernaryRegion, FORWARD_CONDITIONAL_JUMP_OPS,
    BACKWARD_CONDITIONAL_JUMP_OPS, SHORT_CIRCUIT_JUMP_OPS)


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


pyc = sys.argv[1]
name = sys.argv[2]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])
targets = []
find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)

_orig = gen._generate_ternary


def traced(region, *a, **k):
    print('[enter _generate_ternary entry=@%s ctx=%s vt=%s]' % (
        region.entry and region.entry.start_offset,
        getattr(region, 'merge_context', None), getattr(region, 'value_target', None)))
    out = _orig(region, *a, **k)
    print('[exit _generate_ternary entry=@%s] -> %s' % (
        region.entry and region.entry.start_offset,
        json.dumps(out, default=str)[:400]))
    return out


gen._generate_ternary = traced

_orig2 = gen._try_build_orprefix_and_boolop_from_ternary


def traced2(region, cond_expr, tb, fb, *a, **k):
    print('[enter orprefix entry=@%s tb=@%s fb=@%s]' % (
        region.entry and region.entry.start_offset,
        tb and tb.start_offset, fb and fb.start_offset))
    out = _orig2(region, cond_expr, tb, fb, *a, **k)
    print('[exit orprefix] -> %s' % ('None' if out is None else 'HIT'))
    if out is None:
        bo = [r for r in gen.regions if isinstance(r, BoolOpRegion)]
        print('  self.regions boolops: %s' % [
            (r.entry and r.entry.start_offset, r.entry is tb,
             [op for _, op in (r.op_chain or [])],
             r.merge_block and r.merge_block.start_offset,
             r.merge_block is region.merge_block,
             all(op == 'and' for _, op in (r.op_chain or [])))
            for r in bo])
        cb = region.condition_block
        cl = cb and cb.get_last_instruction()
        tgt = cl and cl.argval is not None and gen.cfg.get_block_by_offset(cl.argval)
        print('  chk1 last=%s argval=%s target=@%s is_fvb=%s chain=%s' % (
            cl and cl.opname, cl and cl.argval,
            tgt and tgt.start_offset, tgt is region.false_value_block,
            len(region.condition_chain_blocks or [])))
        for r in gen.regions:
            if isinstance(r, BoolOpRegion) and r.entry is tb:
                full = gen._build_boolop_expression(r)
                print('  full_and_expr=%s' % json.dumps(full, default=str)[:300])
    return out


gen._try_build_orprefix_and_boolop_from_ternary = traced2

try:
    ast = gen.generate()
    print('---- final ----')
    print(json.dumps(ast, default=str)[:6000])
except Exception:
    import traceback
    traceback.print_exc()
