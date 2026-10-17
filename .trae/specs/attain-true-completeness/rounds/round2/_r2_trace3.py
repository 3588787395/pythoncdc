#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: 生成结果 + 区域表达式黑箱检查（fresh，单次 generate 后检查）。

用法:
  python -X utf8 _r2_trace3.py <pyc> <co_name> [--boolops] [--tern]

--boolops: generate() 后对每个 BoolOpRegion 调用 _build_boolop_expression 打印
--tern:    generate() 后对每个 TernaryRegion 打印字段 + _build_ternary_value_expr
"""
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
from core.cfg.region_analyzer import BoolOpRegion, TernaryRegion


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


pyc = sys.argv[1]
name = sys.argv[2]
flags = set(sys.argv[3:])
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])
targets = []
find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)

ast = gen.generate()
print('---- final AST ----')
print(json.dumps(ast, default=str, indent=1)[:8000])

if '--boolops' in flags:
    print('---- boolop exprs ----')
    for r in gen.regions:
        if isinstance(r, BoolOpRegion):
            try:
                e = gen._build_boolop_expression(r)
            except Exception as ex:
                e = 'EXC: %r' % (ex,)
            print('BOOLOP entry=@%s merge=@%s vt=%s chain=%s blocks=%s' % (
                r.entry and r.entry.start_offset,
                r.merge_block and r.merge_block.start_offset,
                getattr(r, 'value_target', None),
                [(o, op) for o, op in (r.op_chain or [])],
                [b.start_offset for b in (r.blocks or [])]))
            print('   expr=%s' % json.dumps(e, default=str)[:600])

if '--tern' in flags:
    print('---- ternary exprs ----')
    for r in gen.regions:
        if isinstance(r, TernaryRegion):
            print('TERN entry=@%s cond=@%s tvb=@%s fvb=@%s merge=@%s ctx=%s vt=%s chain=%s ccops=%s' % (
                r.entry and r.entry.start_offset,
                r.condition_block and r.condition_block.start_offset,
                r.true_value_block and r.true_value_block.start_offset,
                r.false_value_block and r.false_value_block.start_offset,
                r.merge_block and r.merge_block.start_offset,
                getattr(r, 'merge_context', None),
                getattr(r, 'value_target', None),
                [b.start_offset for b in (r.condition_chain_blocks or [])],
                getattr(r, 'chained_compare_ops', None)))
            for _bn in ('true_value_block', 'false_value_block'):
                _blk = getattr(r, _bn)
                if _blk is None:
                    continue
                try:
                    _e = gen._build_ternary_value_expr(_blk)
                except Exception as ex:
                    _e = 'EXC: %r' % (ex,)
                print('   %s=%s' % (_bn, json.dumps(_e, default=str)[:300]))
