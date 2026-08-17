#!/usr/bin/env python3
"""R91 check outer IfRegion type and structure"""
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

# Find the outer IfRegion (entry=108)
outer_if = None
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 108:
        outer_if = r
        break

if outer_if:
    print(f"=== Outer IfRegion (entry=108) ===")
    print(f"  region_type: {outer_if.region_type}")
    print(f"  condition_block: {outer_if.condition_block.start_offset if outer_if.condition_block else '?'}")
    print(f"  then_blocks: {[b.start_offset for b in outer_if.then_blocks]}")
    print(f"  else_blocks: {[b.start_offset for b in outer_if.else_blocks]}")
    print(f"  merge_block: {outer_if.merge_block.start_offset if outer_if.merge_block else '?'}")
    if hasattr(outer_if, 'elif_conditions'):
        print(f"  elif_conditions: {[b.start_offset for b in outer_if.elif_conditions] if outer_if.elif_conditions else []}")
    if hasattr(outer_if, 'elif_bodies'):
        print(f"  elif_bodies: {[[b.start_offset for b in bodies] for bodies in outer_if.elif_bodies] if outer_if.elif_bodies else []}")
    if hasattr(outer_if, 'elif_final_else'):
        print(f"  elif_final_else: {[b.start_offset for b in outer_if.elif_final_else] if outer_if.elif_final_else else []}")
    print(f"  blocks: {[b.start_offset for b in outer_if.blocks]}")
    
    # Also check the nested IfRegion at entry=280
    nested_if = None
    for r in regions:
        if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 280:
            nested_if = r
            break
    if nested_if:
        print(f"\n=== Nested IfRegion (entry=280) ===")
        print(f"  region_type: {nested_if.region_type}")
        print(f"  blocks: {[b.start_offset for b in nested_if.blocks]}")
        print(f"  merge_block: {nested_if.merge_block.start_offset if nested_if.merge_block else '?'}")
        
    # Check what's at offset 438
    block_438 = cfg.get_block_by_offset(438)
    if block_438:
        print(f"\n=== Block 438 ===")
        print(f"  predecessors: {[p.start_offset for p in block_438.predecessors]}")
        print(f"  successors: {[s.start_offset for s in block_438.successors]}")
        # Check which region owns block 438
        owner = analyzer.get_region_for_block(block_438)
        print(f"  owner region: {type(owner).__name__ if owner else 'None'}")
        if owner:
            print(f"  owner entry: {owner.entry.start_offset if owner.entry else '?'}")
