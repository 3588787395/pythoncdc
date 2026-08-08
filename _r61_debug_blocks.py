#!/usr/bin/env python3
"""R61: Debug block 290 and its region"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')

import marshal
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import (RegionAnalyzer, BoolOpRegion, IfRegion, 
    LoopRegion, TernaryRegion)
from pathlib import Path

pyc_path = Path("site-packages/IQEngine/plugins/plugin_system_accounts/position_model/live_future_position.pyc")

with open(pyc_path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

def find_code(code, name):
    if code.co_name == name:
        return code
    for const in code.co_consts:
        if hasattr(const, 'co_name'):
            result = find_code(const, name)
            if result:
                return result
    return None

target_code = find_code(code, 'load_from_kwargs')

# Build CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target_code)

# Analyze regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find block at offset 290
block_290 = cfg.get_block_by_offset(290)
if block_290:
    print(f"=== Block at offset 290 (id={block_290.id}) ===")
    for i in block_290.instructions:
        if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
            argval = getattr(i, 'argval', getattr(i, 'arg', None))
            print(f"  {i.offset:4d} {i.opname:30s} {argval}")
    print(f"  Successors: {[s.start_offset for s in block_290.successors]}")
    print(f"  Predecessors: {[p.start_offset for p in block_290.predecessors]}")
    
    # Check which region owns this block
    print(f"\n=== Regions containing block 290 ===")
    for region in analyzer.regions:
        if block_290 in region.blocks:
            print(f"  {type(region).__name__}: blocks={[b.start_offset for b in region.blocks]}")
            if hasattr(region, 'then_blocks'):
                print(f"    then_blocks={[b.start_offset for b in region.then_blocks]}")
            if hasattr(region, 'else_blocks'):
                print(f"    else_blocks={[b.start_offset for b in region.else_blocks]}")
            if hasattr(region, 'merge_block') and region.merge_block:
                print(f"    merge_block={region.merge_block.start_offset}")
            if hasattr(region, 'entry') and region.entry:
                print(f"    entry={region.entry.start_offset}")
            if hasattr(region, 'body_block') and region.body_block:
                print(f"    body_block={region.body_block.start_offset}")
    
    r = analyzer.get_region_for_block(block_290)
    if r:
        print(f"\n  get_region_for_block: {type(r).__name__}")
else:
    print("Block 290 NOT found!")

# Also check the IfRegion that contains the BoolOp
print("\n=== All IfRegions ===")
for region in analyzer.regions:
    if isinstance(region, IfRegion):
        cond_block = region.condition_block
        cond_offset = cond_block.start_offset if cond_block else None
        then_offsets = [b.start_offset for b in region.then_blocks] if hasattr(region, 'then_blocks') else []
        else_offsets = [b.start_offset for b in region.else_blocks] if hasattr(region, 'else_blocks') else []
        merge = region.merge_block.start_offset if hasattr(region, 'merge_block') and region.merge_block else None
        print(f"  IfRegion: cond={cond_offset} then={then_offsets} else={else_offsets} merge={merge}")

# Check TernaryRegions
print("\n=== All TernaryRegions ===")
for region in analyzer.regions:
    if isinstance(region, TernaryRegion):
        print(f"  TernaryRegion: blocks={[b.start_offset for b in region.blocks]}")
        if hasattr(region, 'entry') and region.entry:
            print(f"    entry={region.entry.start_offset}")
        if hasattr(region, 'merge_block') and region.merge_block:
            print(f"    merge_block={region.merge_block.start_offset}")
