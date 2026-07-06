import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from core.cfg import CFGBuilder, CFGRegionAnalyzer
from core.cfg.region_analyzer import RegionType, LoopRegion

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

    print("=== 所有循环区域 ===")
    for region in analyzer.regions:
        if isinstance(region, LoopRegion):
            print(f"\nLoopRegion:")
            print(f"  header_block: {region.header_block.start_offset}")
            print(f"  entry: {region.entry.start_offset}")
            print(f"  blocks: {[b.start_offset for b in region.blocks]}")
            print(f"  body_blocks: {[b.start_offset for b in region.body_blocks]}")
            print(f"  condition_block: {region.condition_block.start_offset if region.condition_block else 'None'}")
            print(f"  parent: {region.parent.region_type.name if region.parent else 'None'}")
