import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from tests.control_flow_completeness.base import ControlFlowCompletenessTest

# 最小实例：while + if + any()生成器
class TestMinimal(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(grid, target):
    found = False
    if any(target in row for row in grid):
        found = True
    return found
"""

if __name__ == '__main__':
    test = TestMinimal()
    print("=== 原始代码 ===")
    print(test.SOURCE_CODE)

    print("\n=== 反编译结果 ===")
    original = test.compile_source()
    decompiled = test.decompile(original)
    print(decompiled)

    print(f"\n语法正确: {test.verify_syntax_valid()}")
    print(f"字节码等价: {test.verify_bytecode_equivalence()}")
