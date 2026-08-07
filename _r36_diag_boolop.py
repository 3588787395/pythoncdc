#!/usr/bin/env python3
"""Debug: trace _build_boolop_expression for is_stock_trade_trigger."""

import sys, os, marshal, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator

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

# Find BoolOpRegion@490
for r in analyzer.regions:
    if isinstance(r, BoolOpRegion) and r.entry and r.entry.start_offset == 490:
        bor = r
        break

print(f"BoolOpRegion@490:")
print(f"  op_chain={[(b.start_offset, op) for b, op in bor.op_chain]}")
print(f"  blocks={[b.start_offset for b in bor.blocks]}")
print(f"  merge_block={bor.merge_block.start_offset if bor.merge_block else None}")
print(f"  merge_block instructions:")
if bor.merge_block:
    for i in bor.merge_block.instructions:
        print(f"    {i.offset:4d} {i.opname:30s} {i.argval}")

print(f"\n  children={[(type(c).__name__, c.entry.start_offset if c.entry else None) for c in (bor.children or [])]}")

ast_gen = RegionASTGenerator(cfg, analyzer)

# Build boolop expression
print(f"\n=== Building boolop expression ===")
expr = ast_gen._build_boolop_expression(bor)
print(f"  expr = {expr}")

# Check each chain block
for cb, op in bor.op_chain:
    print(f"\n  chain_block@{cb.start_offset} (op={op}):")
    for i in cb.instructions:
        print(f"    {i.offset:4d} {i.opname:30s} {i.argval}")
    
    # Check _try_build_chained_compare_in_boolop
    cc = ast_gen._try_build_chained_compare_in_boolop(cb, bor)
    print(f"    _try_build_chained_compare_in_boolop = {cc}")
