import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
import marshal, dis
from core.cfg.cfg_builder import CFGBuilder

f = open('site-packages/IQEngine/utils/trade_schedule.pyc','rb')
f.read(16)
co = marshal.load(f)

# Find the is_stock_trade_time_now function
for c in co.co_consts:
    if hasattr(c, 'co_code') and c.co_name == 'is_stock_trade_time_now':
        target_co = c
        break

print(f"Function: {target_co.co_name}")
cfg = CFGBuilder().build(target_co)
print(f"\nBlocks:")
for bid, block in sorted(cfg.blocks.items()):
    print(f"\n  Block {bid} (offsets {block.start_offset}-{block.end_offset}):")
    print(f"    Successors: {block.successors}")
    print(f"    Predecessors: {block.predecessors}")
    print(f"    Instructions:")
    for instr in block.instructions:
        print(f"      {instr.offset:4d} {instr.opname:30s} {instr.argval if instr.argval is not None else ''}")

print(f"\nEntry block: {cfg.entry_block_id}")
