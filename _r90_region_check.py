#!/usr/bin/env python3
"""R90 详细检查 block0 在区域结构中的角色"""
import sys, os, marshal, types, json
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator

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

func_code = find_function(orig_code, 'get_kline_by_count_new')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
ast_gen = RegionASTGenerator(cfg, analyzer)

block0 = cfg.get_block_by_offset(0)

print("=== All regions containing block0 ===")
for r in regions:
    if block0 in r.blocks:
        print(f"\n{type(r).__name__}:")
        print(f"  entry: {r.entry.start_offset if hasattr(r, 'entry') and r.entry else '?'}")
        if hasattr(r, 'entry_block') and r.entry_block:
            print(f"  entry_block: {r.entry_block.start_offset}")
        if hasattr(r, 'condition_block') and r.condition_block:
            print(f"  condition_block: {r.condition_block.start_offset}")
        if hasattr(r, 'merge_block') and r.merge_block:
            print(f"  merge_block: {r.merge_block.start_offset}")
        if hasattr(r, 'then_blocks'):
            print(f"  then_blocks: {[b.start_offset for b in r.then_blocks]}")
        if hasattr(r, 'else_blocks'):
            print(f"  else_blocks: {[b.start_offset for b in r.else_blocks]}")
        if hasattr(r, 'op_chain'):
            print(f"  op_chain: {[(b.start_offset if hasattr(b, 'start_offset') else b) for b in r.op_chain]}")
        if hasattr(r, 'value_target'):
            print(f"  value_target: {r.value_target}")
        if hasattr(r, 'parent'):
            print(f"  parent: {type(r.parent).__name__ if r.parent else None}")
        # Check block_to_region mapping
        owner = analyzer.block_to_region.get(block0)
        print(f"  block_to_region owner: {type(owner).__name__ if owner else None}")

print("\n=== Entry region for block0 ===")
entry_region = analyzer.get_entry_region_for_block(block0)
print(f"  {type(entry_region).__name__ if entry_region else None}")

print("\n=== First 5 regions ===")
for i, r in enumerate(regions[:5]):
    print(f"  [{i}] {type(r).__name__}: entry={r.entry.start_offset if hasattr(r, 'entry') and r.entry else '?'}, blocks={[b.start_offset for b in r.blocks][:5]}")
