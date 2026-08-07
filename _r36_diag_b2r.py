#!/usr/bin/env python3
"""Check block_to_region state during AST generation."""

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

# Check block_to_region for specific blocks
block460 = cfg.get_block_by_offset(460)
block492 = cfg.get_block_by_offset(492)
block490 = cfg.get_block_by_offset(490)

print(f"After analyze():")
print(f"  block_to_region has {len(analyzer.block_to_region)} entries")
print(f"  block@460 in block_to_region: {block460 in analyzer.block_to_region}")
print(f"  block@492 in block_to_region: {block492 in analyzer.block_to_region}")
print(f"  block@490 in block_to_region: {block490 in analyzer.block_to_region}")

# Check with get()
r460 = analyzer.block_to_region.get(block460)
r492 = analyzer.block_to_region.get(block492)
r490 = analyzer.block_to_region.get(block490)
print(f"  get(block@460) = {type(r460).__name__ if r460 else None}")
print(f"  get(block@492) = {type(r492).__name__ if r492 else None}")
print(f"  get(block@490) = {type(r490).__name__ if r490 else None}")

# Check if the IfRegion entries match the blocks in block_to_region
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset in (460, 492):
        print(f"\n  {type(r).__name__}@{r.entry.start_offset}:")
        print(f"    entry is block@460? {r.entry is block460}")
        print(f"    entry is block@492? {r.entry is block492}")
        print(f"    entry id={id(r.entry)}")
        print(f"    block@460 id={id(block460)}")
        print(f"    block@492 id={id(block492)}")
        
        # Check if entry is in block_to_region
        print(f"    entry in block_to_region: {r.entry in analyzer.block_to_region}")
        
        # Check if any block with same offset is in block_to_region
        for bk, bk_r in analyzer.block_to_region.items():
            if bk.start_offset == r.entry.start_offset:
                print(f"    found block@{bk.start_offset} (id={id(bk)}) -> {type(bk_r).__name__}")
                print(f"    same object? {bk is r.entry}")

# Now create AST generator and check again
ast_gen = RegionASTGenerator(cfg, analyzer)

# Find IfRegion@102
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 102:
        ifr = r
        break

# Generate then branch (this might modify state)
then_stmts = ast_gen._if_generate_then_branch(ifr)

print(f"\nAfter then branch generation:")
print(f"  block_to_region has {len(analyzer.block_to_region)} entries")
print(f"  block@460 in block_to_region: {block460 in analyzer.block_to_region}")
print(f"  block@492 in block_to_region: {block492 in analyzer.block_to_region}")

r460 = analyzer.block_to_region.get(block460)
r492 = analyzer.block_to_region.get(block492)
print(f"  get(block@460) = {type(r460).__name__ if r460 else None}")
print(f"  get(block@492) = {type(r492).__name__ if r492 else None}")
