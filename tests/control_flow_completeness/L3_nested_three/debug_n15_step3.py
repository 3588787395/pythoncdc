import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from tests.control_flow_completeness.base import ControlFlowCompletenessTest

# 步骤3：while + if + any() + 内层while
class TestStep3(ControlFlowCompletenessTest):
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
    test = TestStep3()
    print("=== 原始代码 ===")
    print(test.SOURCE_CODE)

    print("\n=== 反编译结果 ===")
    original = test.compile_source()
    decompiled = test.decompile(original)
    print(decompiled)

    print(f"\n语法正确: {test.verify_syntax_valid()}")
    print(f"字节码等价: {test.verify_bytecode_equivalence()}")
