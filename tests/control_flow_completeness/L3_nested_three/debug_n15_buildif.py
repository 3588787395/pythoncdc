import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from core.cfg import CFGBuilder, CFGRegionAnalyzer
from core.cfg.region_analyzer import RegionType, IfRegion, LoopRegion
from core.cfg.dominator_analyzer import LoopAnalyzer

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
    
    # 手动运行分析
    analyzer.dom_analyzer.analyze()
    analyzer.loop_analyzer = LoopAnalyzer(cfg, analyzer.dom_analyzer)
    analyzer.loop_analyzer.analyze()
    analyzer.dominance_frontiers = analyzer.dom_analyzer.compute_all_dominance_frontiers()
    
    # Phase 1
    loop_regions = analyzer._identify_loop_regions()
    print(f"Loop regions: {len(loop_regions)}")
    for r in loop_regions:
        print(f"  Loop @ {r.header_block.start_offset}, blocks: {[b.start_offset for b in r.blocks]}")
    
    # Phase 2
    conditional_regions = analyzer._identify_conditional_regions(
        loop_regions=loop_regions,
        try_regions=[],
        with_regions=[],
        match_regions=[],
        boolop_regions=[]
    )
    print(f"\nConditional regions: {len(conditional_regions)}")
    for r in conditional_regions:
        print(f"  If @ {r.entry.start_offset}, blocks: {[b.start_offset for b in r.blocks]}")
        print(f"    then_blocks: {[b.start_offset for b in r.then_blocks]}")
