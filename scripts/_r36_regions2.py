import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
import marshal
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

f = open('site-packages/IQEngine/utils/trade_schedule.pyc','rb')
f.read(16)
co = marshal.load(f)

# Find the is_stock_trade_trigger function
for c in co.co_consts:
    if hasattr(c, 'co_code') and c.co_name == 'is_stock_trade_trigger':
        target_co = c
        break

print(f"Function: {target_co.co_name}")
cfg = CFGBuilder().build(target_co)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print(f"\nRegions ({len(analyzer.regions)}):")
for r in analyzer.regions:
    print(f"\n  {type(r).__name__} (entry={r.entry.start_offset if r.entry else None})")
    print(f"    blocks: {sorted(b.start_offset for b in r.blocks) if r.blocks else 'None'}")
    if hasattr(r, 'condition_block') and r.condition_block:
        print(f"    condition_block: {r.condition_block.start_offset}")
    if hasattr(r, 'merge_block') and r.merge_block:
        print(f"    merge_block: {r.merge_block.start_offset}")
    if hasattr(r, 'then_branch') and r.then_branch:
        print(f"    then_branch: {r.then_branch.start_offset}")
    if hasattr(r, 'else_branch') and r.else_branch:
        print(f"    else_branch: {r.else_branch.start_offset}")
    if hasattr(r, 'op_chain') and r.op_chain:
        print(f"    op_chain: {[(b.start_offset, op) for b, op in r.op_chain]}")
    if hasattr(r, 'chained_compare_ops') and r.chained_compare_ops:
        print(f"    chained_compare_ops: {r.chained_compare_ops}")
    if hasattr(r, 'chained_compare_blocks') and r.chained_compare_blocks:
        print(f"    chained_compare_blocks: {[b.start_offset for b in r.chained_compare_blocks]}")

print(f"\nblock_to_region:")
for block, region in sorted(analyzer.block_to_region.items(), key=lambda x: x[0].start_offset):
    print(f"  block {block.start_offset}: {type(region).__name__} (entry={region.entry.start_offset if region.entry else None})")
