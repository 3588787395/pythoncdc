#!/usr/bin/env python3
"""Diagnose region analysis for get_trading_schedule in IQEngine trade_schedule.pyc."""

import sys, os, marshal, types, dis

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pycdc import PycDecompiler
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

gts = find_code(code, 'get_trading_schedule')

# Build CFG
builder = CFGBuilder()
cfg = builder.build(gts)

# Analyze regions
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
        print(f"    elif_conditions={[b.start_offset for b in r.elif_conditions]}")
        print(f"    elif_bodies={[[b.start_offset for b in body] for body in r.elif_bodies]}")
        print(f"    elif_final_else={[b.start_offset for b in r.elif_final_else]}")
    if isinstance(r, TernaryRegion):
        print(f"    true_value_block={r.true_value_block.start_offset if r.true_value_block else None}")
        print(f"    false_value_block={r.false_value_block.start_offset if r.false_value_block else None}")
        print(f"    merge_block={r.merge_block.start_offset if r.merge_block else None}")
        print(f"    value_target={r.value_target}")
    if isinstance(r, LoopRegion):
        print(f"    condition_block={r.condition_block.start_offset if r.condition_block else None}")
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
