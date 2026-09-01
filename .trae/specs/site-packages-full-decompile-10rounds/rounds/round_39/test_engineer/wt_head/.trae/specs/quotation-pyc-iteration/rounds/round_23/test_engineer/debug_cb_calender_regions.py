"""R23-N9 调试 get_cb_calender_info 的 try-except 前置语句位置"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion

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

# Find the TryExceptRegion around offset 1136
print("=== Regions around 1100-1200 ===")
for region in sorted(analyzer.regions, key=lambda r: r.entry.start_offset if r.entry else 0):
    rtype = type(region).__name__
    entry_off = region.entry.start_offset if region.entry else None
    blocks_off = sorted(b.start_offset for b in region.blocks) if hasattr(region, 'blocks') else []
    if entry_off is not None and 1080 <= entry_off <= 1300:
        print(f"  {rtype} entry={entry_off} blocks={blocks_off}")
        if isinstance(region, TryExceptRegion):
            for attr in ['try_body_blocks', 'handler_blocks', 'try_entry', 'merge_block', 'post_try_blocks']:
                val = getattr(region, attr, None)
                if val is not None:
                    try:
                        if isinstance(val, list):
                            if val and isinstance(val[0], list):
                                print(f"    {attr}: {[[b.start_offset for b in body] for body in val]}")
                            else:
                                print(f"    {attr}: {[b.start_offset for b in val]}")
                        else:
                            print(f"    {attr}: {val.start_offset}")
                    except Exception:
                        print(f"    {attr}: {val}")

# Look at blocks around 1100-1200
print("\n=== Blocks around 1100-1200 ===")
for block in cfg.get_blocks_in_order():
    if 1080 <= block.start_offset <= 1200:
        print(f"\nBlock@{block.start_offset}:")
        for i in block.instructions:
            print(f"  {i.offset:>6} {i.opname:<25} {repr(i.argval)[:60]}")
        print(f"  successors: {[s.start_offset for s in block.successors]}")
        print(f"  predecessors: {[p.start_offset for p in block.predecessors]}")
