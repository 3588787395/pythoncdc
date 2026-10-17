#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: f_b98_compare_cross 生成路径追踪（monkeypatch，只读）。"""
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
from core.cfg.region_analyzer import TernaryRegion, BoolOpRegion


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
regions = gen.region_analyzer.analyze()

print('---- regions of interest ----')
for r in regions:
    if isinstance(r, (TernaryRegion, BoolOpRegion)):
        print('%-14s entry=@%s merge=%s ctx=%s vt=%s op_chain=%s blocks=%s' % (
            type(r).__name__, r.entry and r.entry.start_offset,
            r.merge_block and r.merge_block.start_offset,
            getattr(r, 'merge_context', None), getattr(r, 'value_target', None),
            getattr(r, 'op_chain', None),
            sorted(b.start_offset for b in r.blocks)))

tern = [r for r in regions if isinstance(r, TernaryRegion)]
bo = [r for r in regions if isinstance(r, BoolOpRegion) and r.entry.start_offset == 48]

if tern:
    r = tern[0]
    print('---- direct signature test for ternary entry @%s ----' % r.entry.start_offset)
    print('cond_chain=', [b.start_offset for b in (r.condition_chain_blocks or [])])
    cond_block = r.condition_block
    print('cond_block=@%s last=%s argval=%s' % (
        cond_block and cond_block.start_offset,
        cond_block and cond_block.get_last_instruction().opname,
        cond_block and cond_block.get_last_instruction().argval))
    print('tvb=@%s fvb=@%s merge=@%s' % (
        r.true_value_block and r.true_value_block.start_offset,
        r.false_value_block and r.false_value_block.start_offset,
        r.merge_block and r.merge_block.start_offset))
    if bo:
        br = bo[0]
        full = gen._build_boolop_expression(br)
        print('_build_boolop_expression(boolop@48) =', json.dumps(full, default=str)[:600])
    cond_expr = {'type': 'Name', 'id': 'a'}
    res = gen._try_build_orprefix_and_boolop_from_ternary(
        r, cond_expr, r.true_value_block, r.false_value_block)
    print('_try_build_orprefix_and_boolop_from_ternary ->', json.dumps(res, default=str)[:600])

print('---- trace _generate_ternary ----')
_orig = gen._generate_ternary

def traced(region, *a, **k):
    print('[enter _generate_ternary entry=@%s ctx=%s vt=%s]' % (
        region.entry and region.entry.start_offset,
        getattr(region, 'merge_context', None), getattr(region, 'value_target', None)))
    out = _orig(region, *a, **k)
    print('[exit _generate_ternary entry=@%s] -> %s' % (
        region.entry and region.entry.start_offset, json.dumps(out, default=str)[:500]))
    return out
gen._generate_ternary = traced

_orig2 = gen._try_build_orprefix_and_boolop_from_ternary

def traced2(region, cond_expr, tb, fb, *a, **k):
    out = _orig2(region, cond_expr, tb, fb, *a, **k)
    print('[orprefix entry=@%s cond_last=%s] -> %s' % (
        region.entry and region.entry.start_offset,
        region.condition_block and region.condition_block.get_last_instruction().opname,
        'None' if out is None else 'HIT'))
    if out is None:
        from core.cfg.region_ast_generator import (
            FORWARD_CONDITIONAL_JUMP_OPS, BACKWARD_CONDITIONAL_JUMP_OPS,
            SHORT_CIRCUIT_JUMP_OPS)
        cb = region.condition_block
        cl = cb and cb.get_last_instruction()
        print('  chk1 chain_len=%s last=%s TRUE?=%s in_fwd=%s in_bwd=%s argval=%s' % (
            len(region.condition_chain_blocks or []),
            cl and cl.opname,
            cl and ('TRUE' in cl.opname),
            cl and (cl.opname in (FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS)),
            cl and (cl.argval is not None),
            cl and cl.argval))
        tgt = cl and cl.argval is not None and gen.cfg.get_block_by_offset(cl.argval)
        print('  chk1b target=@%s fvb=@%s is_fvb=%s' % (
            tgt and tgt.start_offset, region.false_value_block and region.false_value_block.start_offset,
            tgt is region.false_value_block))
        hits = [(getattr(r, 'entry', None), r) for r in gen.regions
                if isinstance(r, BoolOpRegion)]
        print('  chk2 boolop regions: %s' % [
            (r.entry and r.entry.start_offset, r.entry is tb,
             [op for _, op in (r.op_chain or [])],
             r.merge_block and r.merge_block.start_offset) for _, r in hits])
        print('  tb=@%s region.merge=@%s' % (
            tb and tb.start_offset, region.merge_block and region.merge_block.start_offset))
        tl = tb and tb.get_last_instruction()
        print('  chk3 tv_last=%s FALSE?=%s short=%s argval=%s' % (
            tl and tl.opname, tl and ('FALSE' in tl.opname),
            tl and (tl.opname in SHORT_CIRCUIT_JUMP_OPS), tl and tl.argval))
        if tl:
            fts = sorted(tb.conditional_successors, key=lambda s: s.start_offset)
            ftb = next((s for s in fts if s.start_offset != tl.argval), None)
            print('  chk3b ft=@%s is_fvb=%s succs=%s' % (
                ftb and ftb.start_offset, ftb is region.false_value_block,
                [s.start_offset for s in fts]))
    return out
gen._try_build_orprefix_and_boolop_from_ternary = traced2

try:
    ast = gen.generate()
    print('---- final AST body ----')
    def walk(s, d=0):
        if isinstance(s, dict):
            t = s.get('type')
            extra = ''
            if t == 'Name':
                extra = s.get('id')
            if t == 'Constant':
                extra = repr(s.get('value'))
            if t == 'BoolOp':
                extra = s.get('op')
            if t == 'UnaryOp':
                extra = s.get('op')
            if t == 'Compare':
                extra = '/'.join(o for o in (s.get('ops') or []))
            print('%s%s %s' % ('  ' * d, t, extra))
            for k in ('body', 'orelse', 'test', 'value', 'values', 'left', 'comparators', 'targets'):
                v = s.get(k)
                if isinstance(v, list):
                    for it in v:
                        walk(it, d + 1)
                elif isinstance(v, dict):
                    walk(v, d + 1)
except Exception:
    import traceback
    traceback.print_exc()
