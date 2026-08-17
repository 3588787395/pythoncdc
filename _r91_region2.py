#!/usr/bin/env python3
"""R91 find the outer IfRegion for get_price_common"""
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

# Show all IfRegions sorted by size
if_regions = [(r, len(r.blocks)) for r in regions if isinstance(r, IfRegion)]
if_regions.sort(key=lambda x: -x[1])

print(f"Total IfRegions: {len(if_regions)}")
for r, size in if_regions[:5]:
    entry = r.entry.start_offset if r.entry else '?'
    cond = r.condition_block.start_offset if r.condition_block else '?'
    then_count = len(r.then_blocks) if r.then_blocks else 0
    else_count = len(r.else_blocks) if r.else_blocks else 0
    else_offsets = [b.start_offset for b in (r.else_blocks or [])][:10]
    print(f"\nIfRegion (size={size}): entry={entry}, cond={cond}")
    print(f"  then_blocks({then_count}): {[b.start_offset for b in (r.then_blocks or [])][:5]}")
    print(f"  else_blocks({else_count}): {else_offsets}")
    # Check if offset 438 is in else_blocks
    if r.else_blocks:
        has_438 = any(b.start_offset == 438 for b in r.else_blocks)
        print(f"  contains offset 438: {has_438}")
