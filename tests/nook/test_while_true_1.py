"""
测试状态: ⚠️ 部分
优先级: P1
相关任务: 任务3.3

描述:
    测试 while True 优化循环的识别

当前问题:
    - Python编译器将 while True: 优化为特殊字节码模式
    - 当前有时会错误识别为无限循环或普通while

期望输出:
    应正确输出 while True: 而不是其他形式
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 基本 while True
TEST_WHILE_TRUE_BASIC = DecompileTestCase(
    name="while_true_basic",
    source_code='''
def loop_until_done():
    while True:
        if is_done():
            break
        process()
'''.strip(),
    expected_patterns=["while True:", "if is_done():", "break", "process()"]
)

# 测试用例2: while True with else
TEST_WHILE_TRUE_ELSE = DecompileTestCase(
    name="while_true_else",
    source_code='''
def search_with_timeout():
    start = time()
    while True:
        if time() - start > 10:
            return None
        if found():
            return result
    else:
        print("loop completed normally")
'''.strip(),
    expected_patterns=["while True:", "if time()", "return", "else:"]
)

# 测试用例3: 嵌套 while True
TEST_WHILE_TRUE_NESTED = DecompileTestCase(
    name="while_true_nested",
    source_code='''
def nested_loops():
    while True:
        setup()
        while True:
            if inner_done():
                break
            process_inner()
        if outer_done():
            break
        process_outer()
'''.strip(),
    expected_patterns=["while True:", "if inner_done():", "break", "if outer_done():"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("WHILE TRUE 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_WHILE_TRUE_BASIC.source_code, "while_true_basic")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_WHILE_TRUE_BASIC, TEST_WHILE_TRUE_ELSE, TEST_WHILE_TRUE_NESTED]:
        success = test.run()
        print(test.get_report())
        print()
