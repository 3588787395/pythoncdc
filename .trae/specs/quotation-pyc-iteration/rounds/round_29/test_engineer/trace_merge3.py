"""R29 测试工程师：追踪repro_r29_12的region类型和merge来源"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, RegionType

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

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

blocks = {b.start_offset: b for b in cfg.get_blocks_in_order()}

print("=== All Regions ===")
for r in regions:
    rtype = r.region_type.name if hasattr(r.region_type, 'name') else str(r.region_type)
    entry_off = r.entry.start_offset
    merge_off = r.merge_block.start_offset if hasattr(r, 'merge_block') and r.merge_block else None
    print(f"  {type(r).__name__}({rtype}): entry={entry_off}, merge={merge_off}")
    if hasattr(r, 'then_blocks') and r.then_blocks:
        print(f"    then={[b.start_offset for b in r.then_blocks]}")
    if hasattr(r, 'else_blocks') and r.else_blocks:
        print(f"    else={[b.start_offset for b in r.else_blocks]}")
    if hasattr(r, 'elif_conditions') and r.elif_conditions:
        print(f"    elif_conditions={[b.start_offset for b in r.elif_conditions]}")
    if hasattr(r, 'elif_bodies') and r.elif_bodies:
        print(f"    elif_bodies={[[b.start_offset for b in body] for body in r.elif_bodies]}")
    if hasattr(r, 'elif_final_else') and r.elif_final_else:
        print(f"    elif_final_else={[b.start_offset for b in r.elif_final_else]}")

# Check which blocks are duplicated across regions
print("\n=== Block ownership check ===")
from collections import Counter
block_counts = Counter()
for r in regions:
    for b in r.blocks:
        block_counts[b.start_offset] += 1
for off, count in sorted(block_counts.items()):
    if count > 1:
        print(f"  block@{off}: owned by {count} regions (VIOLATION)")
