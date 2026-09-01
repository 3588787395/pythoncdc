"""R29 测试工程师：调试repro_r29_12的区域识别"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

SRC = '''def f(x, y, z):
    if x == 1:
        y = 10
    elif x == 2:
        y = 20
    elif x == 3:
        y = 30
    elif x == 4:
        if z:
            return z
        return y
    if y is None:
        return 0
    return y
'''

co = compile(SRC, '<test>', 'exec')
f_co = co.co_consts[0]

builder = CFGBuilder()
cfg = builder.build(f_co)

print(f"=== Blocks (共{len(cfg.blocks)}) ===")
for blk in cfg.get_blocks_in_order():
    last = blk.get_last_instruction()
    last_str = f"{last.opname}→{last.argval}" if last else "None"
    succs = [s.start_offset for s in blk.successors]
    print(f"  blk@{blk.start_offset}: last={last_str}, succs={succs}")
    for ins in blk.instructions:
        if ins.opname in ('EXTENDED_ARG', 'CACHE', 'NOP', 'RESUME'):
            continue
        print(f"    {ins.offset:>4} {ins.opname:<28} {ins.argval}")

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f"\n=== Regions (共{len(regions)}) ===")
for r in regions:
    blocks_str = [b.start_offset for b in r.blocks]
    print(f"  {type(r).__name__}: entry={r.entry.start_offset}, blocks={blocks_str}")
    if hasattr(r, 'then_blocks') and r.then_blocks:
        print(f"    then_blocks: {[b.start_offset for b in r.then_blocks]}")
    if hasattr(r, 'else_blocks') and r.else_blocks:
        print(f"    else_blocks: {[b.start_offset for b in r.else_blocks]}")
    if hasattr(r, 'merge_block') and r.merge_block:
        print(f"    merge_block: {r.merge_block.start_offset}")
    if hasattr(r, 'elif_branches') and r.elif_branches:
        for i, eb in enumerate(r.elif_branches):
            print(f"    elif[{i}]: cond={eb[0].start_offset if eb[0] else None}, blocks={[b.start_offset for b in eb[1]]}")
