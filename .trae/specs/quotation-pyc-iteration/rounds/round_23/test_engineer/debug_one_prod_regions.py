"""R23-N9 调试 one_prod_to_dataframe 的区域分析"""
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
    if isinstance(const, types.CodeType) and const.co_name == 'one_prod_to_dataframe':
        target = const
        break

print(f"Found: {target.co_name}")

builder = CFGBuilder()
cfg = builder.build(target)

print(f"\n=== Blocks (looking around 340-348) ===")
for block in cfg.get_blocks_in_order():
    if block.start_offset >= 320 and block.start_offset <= 380:
        print(f"\nBlock@{block.start_offset}:")
        for i in block.instructions:
            print(f"  {i.offset:>6} {i.opname:<25} {repr(i.argval)[:60]}")
        print(f"  successors: {[s.start_offset for s in block.successors]}")
        print(f"  predecessors: {[p.start_offset for p in block.predecessors]}")

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print(f"\n=== Regions (around 340-412) ===")
for region in sorted(analyzer.regions, key=lambda r: r.entry.start_offset if r.entry else 0):
    rtype = type(region).__name__
    entry_off = region.entry.start_offset if region.entry else None
    blocks_off = sorted(b.start_offset for b in region.blocks) if hasattr(region, 'blocks') else []
    if entry_off is None or (entry_off >= 320 and entry_off <= 420):
        print(f"  {rtype} entry={entry_off} blocks={blocks_off}")
        if isinstance(region, LoopRegion):
            for attr in ['header_block', 'body_blocks', 'for_iter_setup', 'exit_block', 'orelse_block']:
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
