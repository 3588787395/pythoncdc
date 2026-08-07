#!/usr/bin/env python3
"""Debug: trace else branch generation for is_stock_trade_trigger after fix."""

import sys, os, marshal, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator, SHORT_CIRCUIT_JUMP_OPS, FORWARD_CONDITIONAL_JUMP_OPS

PYC_PATH = os.path.join(HERE, 'site-packages', 'IQEngine', 'utils', 'trade_schedule.pyc')

with open(PYC_PATH, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            sub = find_code(const, name)
            if sub:
                return sub
    return None

stt = find_code(code, 'is_stock_trade_trigger')

builder = CFGBuilder()
cfg = builder.build(stt)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find IfRegion@102
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 102:
        ifr = r
        break

ast_gen = RegionASTGenerator(cfg, analyzer)

# Generate then branch first
then_stmts = ast_gen._if_generate_then_branch(ifr)

print(f"generated_blocks after then: {sorted(b.start_offset for b in ast_gen.generated_blocks)}")

# Now trace else branch
print(f"\n=== Tracing else branch ===")

# Patch _generate_region to trace calls
original_generate_region = ast_gen._generate_region
def traced_generate_region(region):
    entry_off = region.entry.start_offset if region.entry else None
    rtype = type(region).__name__
    print(f"  _generate_region({rtype}@{entry_off})")
    if isinstance(region, IfRegion):
        _cb = region.condition_block
        _cb_last = _cb.get_last_instruction() if _cb else None
        _mb = region.merge_block
        _mb_last = _mb.get_last_instruction() if _mb else None
        print(f"    cond_block_last={_cb_last.opname if _cb_last else None}")
        print(f"    merge_block_last={_mb_last.opname if _mb_last else None}")
        print(f"    chained_compare_ops={getattr(region, 'chained_compare_ops', None)}")
    result = original_generate_region(region)
    print(f"    result type={type(result).__name__} len={len(result) if isinstance(result, list) else 1}")
    return result
ast_gen._generate_region = traced_generate_region

else_stmts = ast_gen._if_generate_else_branch(ifr)
print(f"\n  else_stmts = {else_stmts}")
if else_stmts:
    for i, s in enumerate(else_stmts):
        t = s.get('type', '?') if isinstance(s, dict) else '?'
        print(f"  [{i}] type={t}")

# Check generated_blocks after else
print(f"\n  generated_blocks after else: {sorted(b.start_offset for b in ast_gen.generated_blocks)}")

# Check which blocks are NOT generated
all_else = set(ifr.else_blocks)
not_gen = all_else - ast_gen.generated_blocks
print(f"  else_blocks not generated: {sorted(b.start_offset for b in not_gen)}")
