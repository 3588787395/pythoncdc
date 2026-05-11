import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion

src = 'if a and b:\n    x = 1'
code = compile(src, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)
analyzer = RegionAnalyzer(cfg)

# Monkey-patch _build_basic_if_region to trace
orig_build = analyzer._build_basic_if_region
def traced_build(block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None):
    print(f"  _build_basic_if_region: block={block.start_offset}, condition_block={condition_block.start_offset if condition_block else None}")
    return orig_build(block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block)
analyzer._build_basic_if_region = traced_build

regions = analyzer.analyze()

print("\n=== Regions ===")
for r in regions:
    if isinstance(r, IfRegion):
        cond_info = f"cond_block={r.condition_block.start_offset}" if r.condition_block else "no cond"
        print(f"  IfRegion: entry={r.entry.start_offset}, {cond_info}")
