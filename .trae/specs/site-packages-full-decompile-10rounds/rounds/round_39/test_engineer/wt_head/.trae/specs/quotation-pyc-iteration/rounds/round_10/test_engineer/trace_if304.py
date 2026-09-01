#!/usr/bin/env python3
"""精确追踪 get_growth_ability 中 block 304 的处理路径。"""
import sys, marshal, types
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

ORIG_PYC = "/workspace/quotation.pyc"

with open(ORIG_PYC, "rb") as f:
    f.read(16)
    code = marshal.load(f)

def find_code(c, name):
    for const in c.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            r = find_code(const, name)
            if r: return r
    return None

target_code = find_code(code, "get_growth_ability")
cfg = CFGBuilder().build(target_code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# 找 block 304
target_block = None
for b in cfg.blocks.values():
    if b.start_offset == 304:
        target_block = b
        break

# 找外层 IfRegion entry=0
outer_if = None
inner_if = None
for r in analyzer.regions:
    if type(r).__name__ == 'IfRegion':
        if r.entry and r.entry.start_offset == 0:
            outer_if = r
        elif r.entry and r.entry.start_offset == 304:
            inner_if = r

print(f"outer IfRegion: id={id(outer_if)}, entry={outer_if.entry.start_offset}, region_type={outer_if.region_type.name}")
print(f"  else_blocks={[b.start_offset for b in outer_if.else_blocks]}")
print(f"  block 304 in else_blocks: {target_block in outer_if.else_blocks}")
print()

print(f"inner IfRegion: id={id(inner_if)}, entry={inner_if.entry.start_offset}, region_type={inner_if.region_type.name}")
print(f"  blocks={[b.start_offset for b in inner_if.blocks]}")
print(f"  then_blocks={[b.start_offset for b in inner_if.then_blocks]}")
print(f"  else_blocks={[b.start_offset for b in inner_if.else_blocks]}")
print()

# Check get_entry_region_for_block
entry_region = analyzer.get_entry_region_for_block(target_block)
print(f"get_entry_region_for_block(304) = {type(entry_region).__name__ if entry_region else None}")
if entry_region:
    print(f"  entry.start_offset={entry_region.entry.start_offset if entry_region.entry else None}")
    print(f"  id={id(entry_region)}, is inner_if: {entry_region is inner_if}")
print()

# Check get_region_for_block
region_for_block = analyzer.get_region_for_block(target_block)
print(f"get_region_for_block(304) = {type(region_for_block).__name__ if region_for_block else None}")
if region_for_block:
    print(f"  entry.start_offset={region_for_block.entry.start_offset if region_for_block.entry else None}")
print()

# Now check: is block 304 in inner_if's then_blocks or else_blocks?
print(f"block 304 in inner_if.then_blocks: {target_block in inner_if.then_blocks}")
print(f"block 304 in inner_if.else_blocks: {target_block in inner_if.else_blocks}")
print(f"block 304 == inner_if.condition_block: {target_block is inner_if.condition_block}")
print(f"block 304 == inner_if.entry: {target_block is inner_if.entry}")
print()

# Check children of outer_if
print(f"outer_if children:")
for c in (outer_if.children or []):
    print(f"  {type(c).__name__}: entry={c.entry.start_offset if c.entry else None}")
print()

# Check if inner_if is a child of outer_if
print(f"inner_if in outer_if.children: {inner_if in (outer_if.children or [])}")
print(f"inner_if.parent is outer_if: {getattr(inner_if, 'parent', None) is outer_if}")
