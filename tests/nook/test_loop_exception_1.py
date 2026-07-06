"""
测试状态: ⚠️ 部分
优先级: P1
相关任务: 任务3.2

描述:
    测试循环与异常的复杂交互

当前问题:
    - 循环中的 break/continue 在try-except中可能被错误处理
    - 无法正确识别 break/continue 的目标循环

期望输出:
    应正确保留 break/continue 语句
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: for + try + break
TEST_FOR_TRY_BREAK = DecompileTestCase(
    name="for_try_break",
    source_code='''
def search(items):
    for item in items:
        try:
            if check(item):
                return item
        except ValueError:
            break
    return None
'''.strip(),
    expected_patterns=["for item in items:", "try:", "except ValueError:", "break", "return"]
)

# 测试用例2: while + try + continue
TEST_WHILE_TRY_CONTINUE = DecompileTestCase(
    name="while_try_continue",
    source_code='''
def process_all(items):
    results = []
    for item in items:
        try:
            result = process(item)
        except SkipError:
            continue
        except Error:
            break
        results.append(result)
    return results
'''.strip(),
    expected_patterns=["for item in items:", "try:", "except SkipError:", "continue", "except Error:", "break"]
)

# 测试用例3: 嵌套循环 + 异常
TEST_NESTED_LOOP_EXCEPTION = DecompileTestCase(
    name="nested_loop_exception",
    source_code='''
def nested_process(matrix):
    for row in matrix:
        for item in row:
            try:
                process(item)
            except SkipRow:
                break
            except SkipItem:
                continue
'''.strip(),
    expected_patterns=["for row in matrix:", "for item in row:", "break", "continue"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("循环+异常交互字节码示例")
    print("=" * 60)
    disassemble_code(TEST_FOR_TRY_BREAK.source_code, "for_try_break")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_FOR_TRY_BREAK, TEST_WHILE_TRY_CONTINUE, TEST_NESTED_LOOP_EXCEPTION]:
        success = test.run()
        print(test.get_report())
        print()
