"""R23-N8 调试 get_fundflow_day 的区域识别"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, MatchRegion, IfRegion, LoopRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

import types
target = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'get_fundflow_day':
        target = const
        break

print(f"Found: {target.co_name}")

builder = CFGBuilder()
cfg = builder.build(target)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print(f"\n=== Regions (total {len(analyzer.regions)}) ===")
for region in sorted(analyzer.regions, key=lambda r: r.entry.start_offset if r.entry else 0):
    rtype = type(region).__name__
    entry_off = region.entry.start_offset if region.entry else None
    blocks_off = sorted(b.start_offset for b in region.blocks) if hasattr(region, 'blocks') else []
    print(f"  {rtype} entry={entry_off} blocks={blocks_off}")
    if isinstance(region, IfRegion):
        # Show if/elif/else structure
        for attr in ['if_blocks', 'elif_blocks', 'else_blocks', 'then_blocks', 'merge_block']:
            val = getattr(region, attr, None)
            if val is not None:
                try:
                    if isinstance(val, list):
                        offsets = [b.start_offset for b in val]
                    else:
                        offsets = val.start_offset
                    print(f"    {attr}: {offsets}")
                except Exception:
                    print(f"    {attr}: {val}")

print("\n=== All blocks ===")
for block in cfg.get_blocks_in_order():
    print(f"\nBlock@{block.start_offset}:")
    for i in block.instructions:
        print(f"  {i.offset:>6} {i.opname:<25} {repr(i.argval)[:60]}")
    print(f"  successors: {[s.start_offset for s in block.successors]}")
    print(f"  predecessors: {[p.start_offset for p in block.predecessors]}")
