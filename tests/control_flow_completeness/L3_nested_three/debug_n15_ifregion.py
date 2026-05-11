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

    print("=== IF_THEN 区域详情 ===")
    for region in analyzer.regions:
        if region.region_type == RegionType.IF_THEN:
            print(f"IF_THEN @ {region.entry.start_offset}")
            print(f"  then_blocks: {[b.start_offset for b in region.then_blocks]}")
            print(f"  else_blocks: {[b.start_offset for b in region.else_blocks]}")
            print(f"  blocks: {[b.start_offset for b in region.blocks]}")
            print(f"  children: {[c.region_type.name for c in region.children]}")
