#!/usr/bin/env python3
"""R91 check nested IfRegion in else-branch"""
import sys, marshal, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

func_code = find_function(orig_code, 'get_price_common')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Find IfRegion with entry=108 (the outer if)
outer_if = None
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 108:
        outer_if = r
        break

if outer_if:
    print(f"Outer IfRegion: entry=108")
    print(f"  else_blocks: {[b.start_offset for b in outer_if.else_blocks]}")
    
    # Check for nested IfRegions in else_blocks
    else_block_ids = {id(b) for b in outer_if.else_blocks}
    for r in regions:
        if isinstance(r, IfRegion) and r.entry and r.entry.start_offset in [b.start_offset for b in outer_if.else_blocks]:
            print(f"\n  Nested IfRegion in else: entry={r.entry.start_offset}, cond={r.condition_block.start_offset if r.condition_block else '?'}")
            print(f"    then_blocks: {[b.start_offset for b in r.then_blocks]}")
            print(f"    else_blocks: {[b.start_offset for b in r.else_blocks]}")
            print(f"    parent: {type(r.parent).__name__ if r.parent else None}")
    
    # Check blocks NOT in any nested IfRegion
    all_nested_blocks = set()
    for r in regions:
        if isinstance(r, IfRegion) and r.parent is outer_if:
            for b in r.blocks:
                all_nested_blocks.add(b.start_offset)
    
    non_nested_else = [b.start_offset for b in outer_if.else_blocks if b.start_offset not in all_nested_blocks]
    print(f"\n  Non-nested else blocks: {non_nested_else}")
