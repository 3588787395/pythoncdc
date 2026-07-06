"""
测试状态: ❌ 失败
优先级: P0
相关任务: 任务1.5

描述:
    测试 match/case 的或模式匹配
    使用 MATCH_OR 字节码指令

当前问题:
    - 完全不支持 MATCH_OR 指令
    - 无法识别 case 1 | 2 | 3: 这样的或模式

期望输出:
    应包含 case 1 | 2 | 3: 这样的或模式匹配
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 数值或模式
TEST_MATCH_OR_NUMBERS = DecompileTestCase(
    name="match_or_numbers",
    source_code='''
x = 2

match x:
    case 1 | 2 | 3:
        result = "small number"
    case 4 | 5 | 6:
        result = "medium number"
    case 7 | 8 | 9:
        result = "large number"
    case _:
        result = "out of range"
'''.strip(),
    expected_patterns=["match", "case 1 | 2 | 3:", "case 4 | 5 | 6:", "result"]
)

# 测试用例2: 字符串或模式
TEST_MATCH_OR_STRINGS = DecompileTestCase(
    name="match_or_strings",
    source_code='''
command = "start"

match command:
    case "start" | "begin" | "init":
        action = "starting"
    case "stop" | "end" | "quit":
        action = "stopping"
    case "pause" | "suspend":
        action = "pausing"
    case _:
        action = "unknown"
'''.strip(),
    expected_patterns=["match", 'case "start" | "begin" | "init":', "action"]
)

# 测试用例3: 混合或模式
TEST_MATCH_OR_MIXED = DecompileTestCase(
    name="match_or_mixed",
    source_code='''
value = None

match value:
    case None | False | 0 | "" | [] | {}:
        result = "falsy"
    case True | 1 | "yes":
        result = "truthy"
    case _:
        result = "other"
'''.strip(),
    expected_patterns=["match", "case None | False | 0", "result"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("MATCH_OR 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_MATCH_OR_NUMBERS.source_code, "match_or_numbers")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_MATCH_OR_NUMBERS, TEST_MATCH_OR_STRINGS, TEST_MATCH_OR_MIXED]:
        success = test.run()
        print(test.get_report())
        print()
