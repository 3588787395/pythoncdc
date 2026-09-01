"""R29 测试工程师：追踪repro_r29_12的merge计算（analyze后）"""
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

# 先调用analyze
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# 现在检查IPD
blocks = {b.start_offset: b for b in cfg.get_blocks_in_order()}
print("=== Block IPD after analyze() ===")
for off in [0, 14, 20, 32, 38, 50, 56, 68, 72, 76, 80, 84, 88]:
    b = blocks[off]
    ipd = b.immediate_post_dominator
    ipd_off = ipd.start_offset if ipd else None
    print(f"  blk@{off}: ipd={ipd_off}, succs={[s.start_offset for s in b.successors]}")

# 检查block@0的merge
print("\n=== NCPD after analyze ===")
ncpd_0 = analyzer._find_nearest_common_post_dominator(blocks[14], blocks[20])
print(f"  NCPD(14, 20) = {ncpd_0.start_offset if ncpd_0 else None}")

ncpd_38 = analyzer._find_nearest_common_post_dominator(blocks[50], blocks[56])
print(f"  NCPD(50, 56) = {ncpd_38.start_offset if ncpd_38 else None}")

# 检查block@56的else_succ
# block@56: POP_JUMP_FORWARD_IF_FALSE→80, succs=[68, 80]
# then_succ=68, else_succ=80
print(f"\n=== Block@56 merge ===")
ncpd_56 = analyzer._find_nearest_common_post_dominator(blocks[68], blocks[80])
print(f"  NCPD(68, 80) = {ncpd_56.start_offset if ncpd_56 else None}")
print(f"  block@68.IPD = {blocks[68].immediate_post_dominator.start_offset if blocks[68].immediate_post_dominator else None}")
print(f"  block@80.IPD = {blocks[80].immediate_post_dominator.start_offset if blocks[80].immediate_post_dominator else None}")

# 打印_regions中找到的IfRegion
print("\n=== IfRegions ===")
for r in regions:
    if type(r).__name__ == 'IfRegion':
        print(f"  IfRegion@{r.entry.start_offset}: merge={r.merge_block.start_offset if r.merge_block else None}")
        print(f"    then={[b.start_offset for b in r.then_blocks]}")
        print(f"    else={[b.start_offset for b in r.else_blocks]}")
