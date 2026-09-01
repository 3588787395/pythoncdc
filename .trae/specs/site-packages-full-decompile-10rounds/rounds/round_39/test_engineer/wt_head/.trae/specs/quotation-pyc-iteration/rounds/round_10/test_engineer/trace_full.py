#!/usr/bin/env python3
"""精确追踪 block 304 的所有 region 归属和 block_to_region 状态。"""
import sys, marshal, types
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

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

print(f"target_block: id={id(target_block)}, start_offset={target_block.start_offset}")
print()

# 直接检查 block_to_region
print("=== block_to_region direct check ===")
r = analyzer.block_to_region.get(target_block)
print(f"block_to_region[304_obj] = {type(r).__name__ if r else None}")
if r:
    print(f"  entry.start_offset={r.entry.start_offset if r.entry else None}")
    print(f"  region_type={r.region_type.name}")
print()

# 列出所有 region 的 blocks 中包含 target_block 的
print("=== All regions containing target_block ===")
for r in analyzer.regions:
    if target_block in r.blocks:
        print(f"  {type(r).__name__} (id={id(r)}): entry={r.entry.start_offset if r.entry else None}, region_type={r.region_type.name}, blocks_count={len(r.blocks)}")
        print(f"    is_block_entry(304)={r.is_block_entry(target_block)}")
print()

# 列出 block_to_region 中所有 key 的 start_offset
print("=== block_to_region keys (offsets 290-410) ===")
for b, r in analyzer.block_to_region.items():
    if 290 <= b.start_offset <= 410:
        print(f"  block {b.start_offset}: region={type(r).__name__}, entry={r.entry.start_offset if r.entry else None}")
print()

# 检查 IfRegion entry=142 的 elif_conditions
for r in analyzer.regions:
    if type(r).__name__ == 'IfRegion' and r.entry and r.entry.start_offset == 142:
        print(f"=== IfRegion at 142 ===")
        print(f"  region_type={r.region_type.name}")
        print(f"  elif_conditions={[b.start_offset for b in r.elif_conditions] if r.elif_conditions else None}")
        print(f"  elif_bodies={[[b.start_offset for b in body] for body in r.elif_bodies] if r.elif_bodies else None}")
        print(f"  blocks={[b.start_offset for b in r.blocks]}")
        print(f"  then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks={[b.start_offset for b in r.else_blocks]}")
        print(f"  block 304 in r.blocks: {target_block in r.blocks}")
