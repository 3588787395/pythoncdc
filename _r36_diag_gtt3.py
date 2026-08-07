#!/usr/bin/env python3
"""Debug: trace _generate_block_statements for block 74 in get_trading_time_tuple."""

import sys, os, marshal, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, BlockRole
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

gtt = find_code(code, 'get_trading_time_tuple')

builder = CFGBuilder()
cfg = builder.build(gtt)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

block74 = cfg.get_block_by_offset(74)
print(f"=== Block@74 ===")
print(f"  instructions: {len(block74.instructions)}")
for i in block74.instructions:
    print(f"  {i.offset:4d} {i.opname:30s} {i.argval}")

print(f"\n  block_role: {analyzer.get_block_role(block74)}")

# Check effective_instructions
eff = analyzer.effective_instructions.get(block74.start_offset)
print(f"\n  effective_instructions: {len(eff) if eff else 'None'}")
if eff:
    for i in eff:
        print(f"  {i.offset:4d} {i.opname:30s} {i.argval}")

# Check parent-child
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 36:
        print(f"\n=== IfRegion@36 ===")
        print(f"  parent: {type(r.parent).__name__}@{r.parent.entry.start_offset if r.parent and r.parent.entry else None}")
        print(f"  children: {[(type(c).__name__, c.entry.start_offset if c.entry else None) for c in (r.children or [])]}")
    if isinstance(r, LoopRegion) and r.entry and r.entry.start_offset == 34:
        print(f"\n=== LoopRegion@34 ===")
        print(f"  parent: {type(r.parent).__name__}@{r.parent.entry.start_offset if r.parent and r.parent.entry else None}")
        print(f"  children: {[(type(c).__name__, c.entry.start_offset if c.entry else None) for c in (r.children or [])]}")
