#!/usr/bin/env python3
"""Debug: check children of IfRegion@102."""

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

# Find IfRegion@102
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 102:
        ifr = r
        break

print(f"IfRegion@102:")
print(f"  children: {[(type(c).__name__, c.entry.start_offset if c.entry else None) for c in (ifr.children or [])]}")
print(f"  else_blocks: {[b.start_offset for b in ifr.else_blocks]}")

# Check if BoolOpRegion@490 is in children
for c in (ifr.children or []):
    if isinstance(c, BoolOpRegion):
        print(f"  Found BoolOpRegion child: entry={c.entry.start_offset}")

# Check all regions that have entry in else_blocks
print(f"\n=== Regions with entry in else_blocks ===")
else_block_set = set(ifr.else_blocks)
for r in analyzer.regions:
    if r.entry and r.entry in else_block_set:
        print(f"  {type(r).__name__}: entry={r.entry.start_offset}, blocks={[b.start_offset for b in r.blocks]}")
