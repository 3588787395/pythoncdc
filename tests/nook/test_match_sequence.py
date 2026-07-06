"""
测试状态: ❌ 失败
优先级: P0
相关任务: 任务1.3

描述:
    测试 match/case 的序列模式匹配
    使用 MATCH_SEQUENCE 字节码指令

当前问题:
    - 完全不支持 MATCH_SEQUENCE 指令
    - 无法识别 [] / [single] / [first, *rest] 等序列模式

期望输出:
    应包含 case []:, case [single]:, case [first, *rest]: 等序列模式
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 列表模式
TEST_MATCH_SEQUENCE_LIST = DecompileTestCase(
    name="match_sequence_list",
    source_code='''
items = [1, 2, 3]

match items:
    case []:
        result = "empty"
    case [single]:
        result = f"one item: {single}"
    case [first, second]:
        result = f"two items: {first}, {second}"
    case [first, *rest]:
        result = f"first: {first}, rest: {rest}"
    case _:
        result = "other"
'''.strip(),
    expected_patterns=["match", "case []:", "case [single]:", "case [first, *rest]:", "result"]
)

# 测试用例2: 元组模式
TEST_MATCH_SEQUENCE_TUPLE = DecompileTestCase(
    name="match_sequence_tuple",
    source_code='''
point = (1, 2)

match point:
    case (0, 0):
        result = "origin"
    case (x, 0):
        result = f"on x-axis at {x}"
    case (0, y):
        result = f"on y-axis at {y}"
    case (x, y):
        result = f"point at ({x}, {y})"
'''.strip(),
    expected_patterns=["match", "case (0, 0):", "case (x, y):", "result"]
)

# 测试用例3: 带星号的序列解包
TEST_MATCH_SEQUENCE_STAR = DecompileTestCase(
    name="match_sequence_star",
    source_code='''
values = [1, 2, 3, 4, 5]

match values:
    case [*all]:
        result = f"all: {all}"
    case [first, *middle, last]:
        result = f"first={first}, middle={middle}, last={last}"
    case [first, second, *rest]:
        result = f"first={first}, second={second}, rest={rest}"
'''.strip(),
    expected_patterns=["match", "case [*all]:", "case [first, *middle, last]:", "result"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("MATCH_SEQUENCE 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_MATCH_SEQUENCE_LIST.source_code, "match_sequence_list")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_MATCH_SEQUENCE_LIST, TEST_MATCH_SEQUENCE_TUPLE, TEST_MATCH_SEQUENCE_STAR]:
        success = test.run()
        print(test.get_report())
        print()
