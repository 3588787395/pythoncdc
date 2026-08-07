#!/usr/bin/env python3
"""Debug: check block 74 instructions in get_trading_time_tuple."""

import sys, os, marshal, types, dis

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion

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

gtt = find_code(code, 'get_trading_time_tuple')

builder = CFGBuilder()
cfg = builder.build(gtt)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Print all blocks with their instructions
for block in cfg.get_blocks_in_order():
    print(f"\n=== block@{block.start_offset} ===")
    print(f"  succs={[s.start_offset for s in block.successors]}")
    for instr in block.instructions:
        print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argval}")

# Check IfRegion@36
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 36:
        print(f"\n=== IfRegion@36 ===")
        print(f"  then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks={[b.start_offset for b in r.else_blocks]}")
        print(f"  merge_block={r.merge_block.start_offset if r.merge_block else None}")
        print(f"  blocks={[b.start_offset for b in r.blocks]}")
        
        # Check if block 74 is correctly identified
        block74 = cfg.get_block_by_offset(74)
        print(f"\n  block@74 instructions count: {len(block74.instructions)}")
        print(f"  block@74 start_offset: {block74.start_offset}")
