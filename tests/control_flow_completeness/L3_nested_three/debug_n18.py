import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

from tests.control_flow_completeness.base import ControlFlowCompletenessTest

class TestN18_TryForIfTryExcept(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(data_groups):
    all_results = []
    try:
        for group in data_groups:
            group_results = []
            for value in group:
                try:
                    if value < 0:
                        raise ValueError("negative")
                    parsed = str(value)
                except ValueError:
                    parsed = "NEG"
                group_results.append(parsed)
            all_results.append(group_results)
    except Exception:
        all_results = [["ERROR"]]
    return all_results
"""

if __name__ == '__main__':
    test = TestN18_TryForIfTryExcept()

    print("=== 原始代码 ===")
    print(test.SOURCE_CODE)

    print("\n=== 反编译结果 ===")
    original = test.compile_source()
    decompiled = test.decompile(original)
    print(decompiled)

    print("\n=== 语法验证 ===")
    print(f"语法正确: {test.verify_syntax_valid()}")

    print("\n=== 字节码等价性 ===")
    print(f"字节码等价: {test.verify_bytecode_equivalence()}")
