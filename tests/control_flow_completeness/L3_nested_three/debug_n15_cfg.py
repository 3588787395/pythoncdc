import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from core.cfg import CFGBuilder

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
    
    print("=== CFG Blocks ===")
    for block in cfg.blocks.values():
        print(f"\nBlock @{block.start_offset}:")
        print(f"  instructions: {[i.opname for i in block.instructions]}")
        print(f"  successors: {[b.start_offset for b in block.successors]}")
        print(f"  predecessors: {[b.start_offset for b in block.predecessors]}")
