#!/usr/bin/env python3
"""Diagnose get_trading_time_tuple region analysis."""

import sys, os, marshal, types, dis

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, TernaryRegion, BoolOpRegion, LoopRegion

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

print("=== All Regions ===")
for r in analyzer.regions:
    blocks_info = [b.start_offset for b in r.blocks] if hasattr(r, 'blocks') else []
    entry = r.entry.start_offset if r.entry else None
    print(f"  {type(r).__name__}: entry={entry}, blocks={blocks_info}")
    if isinstance(r, IfRegion):
        print(f"    condition_block={r.condition_block.start_offset if r.condition_block else None}")
        print(f"    then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")
        print(f"    merge_block={r.merge_block.start_offset if r.merge_block else None}")
    if isinstance(r, LoopRegion):
        print(f"    header_block={r.header_block.start_offset if r.header_block else None}")
        print(f"    body_blocks={[b.start_offset for b in r.body_blocks] if hasattr(r, 'body_blocks') else 'N/A'}")

print("\n=== Block to Region mapping ===")
for block, region in sorted(analyzer.block_to_region.items(), key=lambda x: x[0].start_offset):
    print(f"  block@{block.start_offset} -> {type(region).__name__}(entry={region.entry.start_offset if region.entry else None})")

print("\n=== CFG Blocks ===")
for block in cfg.get_blocks_in_order():
    last = block.get_last_instruction()
    succs = [s.start_offset for s in block.successors]
    cond_succs = [s.start_offset for s in block.conditional_successors]
    print(f"  block@{block.start_offset}: last={last.opname if last else None}({last.argval if last else None}), succs={succs}, cond_succs={cond_succs}")
