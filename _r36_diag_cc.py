#!/usr/bin/env python3
"""Debug: check IfRegion@460 chained_compare fields."""

import sys, os, marshal, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion

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

# Find IfRegion@460
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 460:
        ifr = r
        break

print(f"IfRegion@460:")
print(f"  entry={ifr.entry.start_offset}")
print(f"  blocks={[b.start_offset for b in ifr.blocks]}")
print(f"  condition_block={ifr.condition_block.start_offset if ifr.condition_block else None}")
print(f"  merge_block={ifr.merge_block.start_offset if ifr.merge_block else None}")
print(f"  else_blocks={[b.start_offset for b in ifr.else_blocks]}")
print(f"  chained_compare_ops={getattr(ifr, 'chained_compare_ops', 'MISSING')}")
print(f"  chained_compare_blocks={[b.start_offset for b in getattr(ifr, 'chained_compare_blocks', [])]}")
print(f"  chained_left_instr={getattr(ifr, 'chained_left_instr', 'MISSING')}")
print(f"  chained_comparator_instrs={getattr(ifr, 'chained_comparator_instrs', 'MISSING')}")

# Check block identity
block_490 = cfg.get_block_by_offset(490)
print(f"\n  merge_block is block@490: {ifr.merge_block is block_490}")
print(f"  merge_block id: {id(ifr.merge_block)}")
print(f"  block@490 id: {id(block_490)}")

# Find BoolOpRegion@490
for r in analyzer.regions:
    if isinstance(r, BoolOpRegion) and r.entry and r.entry.start_offset == 490:
        bor = r
        break

print(f"\nBoolOpRegion@490:")
print(f"  op_chain={[(b.start_offset, op) for b, op in bor.op_chain]}")
chain_block_490 = bor.op_chain[0][0]
print(f"  chain_block@490 id: {id(chain_block_490)}")
print(f"  chain_block@490 is block@490: {chain_block_490 is block_490}")
print(f"  ifr.merge_block is chain_block@490: {ifr.merge_block is chain_block_490}")

# Now try _try_build_chained_compare_in_boolop manually
from core.cfg.region_ast_generator import RegionASTGenerator
ast_gen = RegionASTGenerator(cfg, analyzer)

# Check the first loop
print(f"\n=== First loop in _try_build_chained_compare_in_boolop ===")
for r in ast_gen.regions:
    if isinstance(r, IfRegion):
        if r.entry is chain_block_490:
            print(f"  Found IfRegion with entry == chain_block@490: entry={r.entry.start_offset}")
            print(f"    condition_block is chain_block: {r.condition_block is chain_block_490}")
            print(f"    chained_compare_ops: {getattr(r, 'chained_compare_ops', None)}")

# Check the second loop
print(f"\n=== Second loop in _try_build_chained_compare_in_boolop ===")
for r in ast_gen.regions:
    if isinstance(r, IfRegion):
        if getattr(r, 'merge_block', None) is chain_block_490:
            print(f"  Found IfRegion with merge_block == chain_block@490: entry={r.entry.start_offset}")
            print(f"    chained_compare_ops: {getattr(r, 'chained_compare_ops', None)}")
            print(f"    chained_compare_blocks: {[b.start_offset for b in getattr(r, 'chained_compare_blocks', [])]}")
