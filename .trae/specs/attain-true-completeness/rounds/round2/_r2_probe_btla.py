#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: probe value-diamond arm builders for b_ternary_lhs_and (item b)."""
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
from core.cfg.region_analyzer import BoolOpRegion, IfRegion, TernaryRegion

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

blk = {b.start_offset: b for b in cfg.get_all_blocks()} if hasattr(cfg, 'get_all_blocks') else {}
if not blk:
    _cand = cfg.blocks
    if isinstance(_cand, dict):
        for _k, _v in _cand.items():
            if hasattr(_v, 'start_offset'):
                blk[_v.start_offset] = _v
    else:
        for _v in _cand:
            if hasattr(_v, 'start_offset'):
                blk[_v.start_offset] = _v


def d(expr, depth=0):
    if expr is None:
        return 'None'
    if not isinstance(expr, dict):
        return repr(expr)
    t = expr.get('type')
    pad = '  ' * depth
    if t == 'Name':
        return pad + 'Name(%s)' % expr.get('id')
    if t == 'Constant':
        return pad + 'Const(%r)' % (expr.get('value'),)
    if t == 'BoolOp':
        return pad + 'BoolOp(%s, [%s])' % (expr.get('op'),
                                           ', '.join(d(v, 0) for v in expr.get('values', [])))
    if t == 'IfExp':
        return (pad + 'IfExp(\n' + d(expr.get('test'), depth + 1) + ',\n'
                + d(expr.get('body'), depth + 1) + ',\n'
                + d(expr.get('orelse'), depth + 1) + ')')
    if t == 'UnaryOp':
        return pad + 'UnaryOp(%s, %s)' % (expr.get('op'), d(expr.get('operand'), 0))
    return pad + repr(expr)


# region set without generate() side effects: use analyzer directly
gen.region_analyzer.analyze()
regs = gen.region_analyzer.regions
print('---- regions (pre-generate) ----')
for r in regs:
    print('  %s entry=@%s merge=@%s blocks=%s' % (
        type(r).__name__,
        getattr(r, 'entry', None) and r.entry.start_offset,
        getattr(r, 'merge_block', None) and getattr(r.merge_block, 'start_offset', None),
        sorted(b.start_offset for b in getattr(r, 'blocks', None) or [])))

# BoolOpRegion@10 for b_ternary_lhs_and
bo = None
ifr = None
for r in regs:
    if isinstance(r, BoolOpRegion) and r.entry.start_offset == 10:
        bo = r
    if isinstance(r, IfRegion) and r.entry.start_offset == 0:
        ifr = r
print('---- probes ----')
if bo is not None:
    print('value_target=%r merge_context=%r' % (getattr(bo, 'value_target', None),
                                                getattr(bo, 'merge_context', None)))
    try:
        e = gen._build_boolop_expression(bo)
        print('_build_boolop_expression(BO@10):')
        print(d(e, 1))
    except Exception as ex:
        print('_build_boolop_expression(BO@10) EXC %r' % (ex,))
else:
    print('no BoolOpRegion@10')
for off in (6, 10):
    try:
        e = gen._build_value_block_expr(blk[off])
        print('_build_value_block_expr(@%d):' % off)
        print(d(e, 1))
    except Exception as ex:
        print('_build_value_block_expr(@%d) EXC %r' % (off, ex))
if ifr is not None:
    print('IfRegion@0: cond=@%s merge=@%s then=%s else=%s' % (
        ifr.condition_block.start_offset,
        ifr.merge_block.start_offset,
        sorted(b.start_offset for b in ifr.then_blocks or []),
        sorted(b.start_offset for b in ifr.else_blocks or [])))
    try:
        res = gen._try_build_value_diamond_return(ifr)
        print('_try_build_value_diamond_return ->', d(res[0], 1) if res else None)
    except Exception as ex:
        print('_try_build_value_diamond_return EXC %r' % (ex,))
