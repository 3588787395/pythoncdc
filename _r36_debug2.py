#!/usr/bin/env python3
"""Debug: trace which code path generates LoopRegion@360 in then branch."""

import sys, os, marshal, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, TernaryRegion, BoolOpRegion, LoopRegion
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

gts = find_code(code, 'get_trading_schedule')

builder = CFGBuilder()
cfg = builder.build(gts)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find IfRegion@66
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 66:
        ifr = r
        break

ast_gen = RegionASTGenerator(cfg, analyzer)

# Check _is_child_reachable_from_blocks for each child
print("=== Checking child reachability from then_blocks ===")
then_blocks_set = set(ifr.then_blocks)
for child in (ifr.children or []):
    entry_off = child.entry.start_offset if child.entry else None
    reachable = ast_gen._is_child_reachable_from_blocks(child, ifr.then_blocks)
    entry_in_then = child.entry in then_blocks_set if child.entry else False
    entry_in_else = child.entry in set(ifr.else_blocks) if child.entry else False
    
    # Check offset overlap
    then_min = min(b.start_offset for b in ifr.then_blocks)
    then_max = max(b.start_offset for b in ifr.then_blocks)
    child_offsets = {b.start_offset for b in child.blocks}
    has_overlap = any(then_min <= bo <= then_max for bo in child_offsets)
    
    print(f"  {type(child).__name__}@{entry_off}: reachable={reachable}, entry_in_then={entry_in_then}, entry_in_else={entry_in_else}, offset_overlap={has_overlap}")
    print(f"    child.blocks={[b.start_offset for b in child.blocks]}")
    print(f"    then_blocks range: {then_min}-{then_max}")

# Now trace the _if_generate_then_branch processing
print("\n=== Tracing _if_generate_then_branch ===")

# Patch _generate_region to trace calls
original_generate_region = ast_gen._generate_region
def traced_generate_region(region):
    entry_off = region.entry.start_offset if region.entry else None
    print(f"  _generate_region called for {type(region).__name__}@{entry_off}")
    result = original_generate_region(region)
    print(f"  _generate_region returned: {type(result).__name__} with {len(result) if isinstance(result, list) else 1} item(s)")
    return result
ast_gen._generate_region = traced_generate_region

then_stmts = ast_gen._if_generate_then_branch(ifr)
print(f"\n  then_stmts has {len(then_stmts)} items")
for i, s in enumerate(then_stmts):
    t = s.get('type', '?') if isinstance(s, dict) else '?'
    print(f"    [{i}] type={t}")
    if t == 'For':
        iter_args = s.get('iter', {}).get('args', [])
        print(f"        range args: {iter_args}")

print(f"\n  generated_blocks after then: {sorted(b.start_offset for b in ast_gen.generated_blocks)}")
