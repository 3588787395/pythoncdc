"""R23-N9 调试 get_cb_calender_info 的区域层级和块1120归属"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, LoopRegion, IfRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

import types
target = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'get_cb_calender_info':
        target = const
        break

builder = CFGBuilder()
cfg = builder.build(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Show all regions with parent info
print("=== All regions with parent info ===")
for region in sorted(analyzer.regions, key=lambda r: r.entry.start_offset if r.entry else 0):
    rtype = type(region).__name__
    entry_off = region.entry.start_offset if region.entry else None
    parent_off = region.parent.entry.start_offset if region.parent else None
    blocks_off = sorted(b.start_offset for b in region.blocks) if hasattr(region, 'blocks') else []
    print(f"  {rtype} entry={entry_off} parent={parent_off} blocks={blocks_off[:10]}...")

# Check which region owns block 1120
print("\n=== Block 1120 ownership ===")
block_1120 = cfg.blocks.get(1120)
if block_1120:
    print(f"Block@1120: {block_1120}")
    for region in analyzer.regions:
        if block_1120 in region.blocks:
            print(f"  In region: {type(region).__name__} entry={region.entry.start_offset if region.entry else None}")
    # Check block_to_region mapping
    r = analyzer.block_to_region.get(block_1120)
    if r:
        print(f"  block_to_region: {type(r).__name__} entry={r.entry.start_offset if r.entry else None}")
    else:
        print(f"  block_to_region: None")

# Check top-level regions
print("\n=== Top-level regions ===")
for r in analyzer.regions:
    if r.parent is None:
        rtype = type(r).__name__
        entry_off = r.entry.start_offset if r.entry else None
        blocks_off = sorted(b.start_offset for b in r.blocks) if hasattr(r, 'blocks') else []
        print(f"  {rtype} entry={entry_off} blocks={blocks_off[:15]}...")
