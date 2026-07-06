import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from core.cfg import CFGBuilder, CFGRegionAnalyzer
from core.cfg.region_analyzer import RegionType, IfRegion, LoopRegion

SOURCE_CODE = """
def test_func(grids, target):
    pos = None
    gi = 0
    while gi < len(grids):
        grid = grids[gi]
        if any(target in row for row in grid):
            gj = 0
            while gj < len(grid):
                gj += 1
        gi += 1
    return pos
"""

if __name__ == '__main__':
    code_obj = compile(SOURCE_CODE, '<test>', 'exec')
    func_code = None
    for const in code_obj.co_consts:
        if hasattr(const, 'co_name') and const.co_name != '<module>':
            func_code = const
            break

    cfg = CFGBuilder().build(func_code)
    analyzer = CFGRegionAnalyzer(cfg)
    analyzer.analyze()

    print("=== 识别的区域 ===")
    for region in analyzer.regions:
        print(f"\n{region.region_type.name} @ {region.entry.start_offset if hasattr(region, 'entry') else 'N/A'}")
        print(f"  blocks: {[b.start_offset for b in region.blocks]}")
        if hasattr(region, 'condition_block') and region.condition_block:
            print(f"  condition_block: {region.condition_block.start_offset}")
        if hasattr(region, 'then_blocks'):
            print(f"  then_blocks: {[b.start_offset for b in region.then_blocks]}")
        if hasattr(region, 'else_blocks'):
            print(f"  else_blocks: {[b.start_offset for b in region.else_blocks]}")
        if hasattr(region, 'body_blocks'):
            print(f"  body_blocks: {[b.start_offset for b in region.body_blocks]}")
        if hasattr(region, 'header_block'):
            print(f"  header_block: {region.header_block.start_offset}")

    print("\n=== block_to_region 映射 ===")
    for offset in sorted(analyzer.block_to_region.keys(), key=lambda b: b.start_offset):
        region = analyzer.block_to_region[offset]
        print(f"  block@{offset.start_offset} -> {region.region_type.name}")
