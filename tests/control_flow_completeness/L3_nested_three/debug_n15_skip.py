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

    if_region = None
    loop_region = None
    for region in analyzer.regions:
        if isinstance(region, IfRegion):
            if_region = region
        elif isinstance(region, LoopRegion) and region.header_block.start_offset == 162:
            loop_region = region

    if if_region and loop_region:
        print(f"IF_THEN blocks: {[b.start_offset for b in if_region.blocks]}")
        print(f"WHILE_LOOP blocks: {[b.start_offset for b in loop_region.blocks]}")
        print(f"loop.blocks <= if.blocks: {loop_region.blocks <= if_region.blocks}")
        print(f"_should_skip_nesting: {analyzer._should_skip_nesting(loop_region, if_region)}")
