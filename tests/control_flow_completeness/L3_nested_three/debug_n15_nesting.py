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

    # 手动检查嵌套关系
    if_regions = [r for r in analyzer.regions if isinstance(r, IfRegion)]
    loop_regions = [r for r in analyzer.regions if isinstance(r, LoopRegion)]

    print("=== 手动检查嵌套关系 ===")
    for if_region in if_regions:
        for loop_region in loop_regions:
            if loop_region == if_region:
                continue
            print(f"\nIF_THEN@{if_region.entry.start_offset} vs WHILE_LOOP@{loop_region.header_block.start_offset}")
            print(f"  loop.blocks <= if.blocks: {loop_region.blocks <= if_region.blocks}")
            print(f"  loop.entry in if.blocks: {loop_region.entry in if_region.blocks}")
            print(f"  loop.header_block in if.then_blocks: {loop_region.header_block in if_region.then_blocks}")
            print(f"  loop.blocks & set(if.then_blocks): {loop_region.blocks & set(if_region.then_blocks)}")

            # 检查_should_skip_nesting
            skip = analyzer._should_skip_nesting(loop_region, if_region)
            print(f"  _should_skip_nesting: {skip}")
