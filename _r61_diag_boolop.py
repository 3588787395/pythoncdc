#!/usr/bin/env python3
"""R61 Test Engineer: Check if BoolOpRegion is detected for load_from_kwargs."""
import sys, os
sys.path.insert(0, r'f:\Downloads\pythoncdc-main')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.dominator_analyzer import DominatorAnalyzer

PYC_PATH = r"site-packages\IQEngine\plugins\plugin_system_accounts\position_model\live_future_position.pyc"

# Load the pyc
import marshal, types
with open(PYC_PATH, 'rb') as f:
    magic = f.read(4)
    f.read(12)
    code = marshal.load(f)

# Find load_from_kwargs
def find_code(co, name):
    if co.co_name == name:
        return co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            result = find_code(const, name)
            if result:
                return result
    return None

target_co = find_code(code, 'load_from_kwargs')
if not target_co:
    print("load_from_kwargs not found!")
    sys.exit(1)

print(f"Found load_from_kwargs: {len(target_co.co_code)} bytes")

# Build CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target_co, 'load_from_kwargs')
print(f"CFG blocks: {len(cfg.blocks)}")

# Build dominator tree
dom_analyzer = DominatorAnalyzer(cfg)
dom_analyzer.analyze()

# Analyze regions
region_analyzer = RegionAnalyzer(cfg, dom_analyzer)
regions = region_analyzer.analyze()

print(f"\nRegions found: {len(regions)}")
from core.cfg.region_analyzer import BoolOpRegion, IfRegion, LoopRegion, TryExceptRegion
for r in regions:
    rtype = type(r).__name__
    entry = r.entry.start_offset if r.entry else '?'
    blocks = [b.start_offset for b in r.blocks]
    print(f"  {rtype} entry={entry} blocks={blocks}")
    if isinstance(r, BoolOpRegion):
        print(f"    op_chain={[(b.start_offset, op) for b, op in r.op_chain]}")
        print(f"    merge_block={r.merge_block.start_offset if r.merge_block else None}")
        print(f"    value_target={getattr(r, 'value_target', None)}")
        print(f"    prefix_block={r.prefix_block.start_offset if r.prefix_block else None}")

# Check block_to_region mapping for the critical blocks
print(f"\nblock_to_region mapping (critical area):")
for block in cfg.get_blocks_in_order():
    if 220 <= block.start_offset <= 290:
        r = region_analyzer.block_to_region.get(block)
        rtype = type(r).__name__ if r else 'None'
        instrs = [i.opname for i in block.instructions[:5]]
        print(f"  block@{block.start_offset} -> {rtype}  instrs={instrs}...")
