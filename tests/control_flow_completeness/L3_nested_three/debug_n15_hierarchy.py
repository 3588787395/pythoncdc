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

    print("=== 区域层次结构 ===")
    for region in analyzer.regions:
        parent_type = region.parent.region_type.name if region.parent else "None"
        children_types = [c.region_type.name for c in region.children]
        print(f"\n{region.region_type.name} @ {region.entry.start_offset if hasattr(region, 'entry') else 'N/A'}")
        print(f"  parent: {parent_type}")
        print(f"  children: {children_types}")
