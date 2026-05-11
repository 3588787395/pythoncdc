"""
测试状态: ❌ 失败
优先级: P0
相关任务: 任务1.1

描述:
    测试基本的 match/case 语法 - 值模式匹配
    使用 MATCH_VALUE 字节码指令

当前问题:
    - 完全不支持 MATCH_VALUE 指令
    - 反编译器无法识别 match 结构
    - 输出中不包含 match/case 关键字

期望输出:
    应包含正确的 match x: 和 case 1: / case 2: / case _: 结构
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 基本值匹配
TEST_MATCH_VALUE = DecompileTestCase(
    name="match_value_basic",
    source_code='''
x = 1
match x:
    case 1:
        result = "one"
    case 2:
        result = "two"
    case _:
        result = "other"
'''.strip(),
    expected_patterns=["match", "case 1:", "case 2:", "case _:"]
)

# 测试用例2: 字符串匹配
TEST_MATCH_STRING = DecompileTestCase(
    name="match_string",
    source_code='''
command = "start"
match command:
    case "start":
        action = "starting"
    case "stop":
        action = "stopping"
    case "restart":
        action = "restarting"
    case _:
        action = "unknown"
'''.strip(),
    expected_patterns=["match", 'case "start":', 'case "stop":', 'case _:', "action"]
)

# 测试用例3: 常量匹配
TEST_MATCH_CONSTANTS = DecompileTestCase(
    name="match_constants",
    source_code='''
value = None
match value:
    case None:
        result = "null"
    case True:
        result = "true"
    case False:
        result = "false"
    case _:
        result = "other"
'''.strip(),
    expected_patterns=["match", "case None:", "case True:", "case False:", "case _:"]
)


if __name__ == "__main__":
    # 显示字节码
    print("=" * 60)
    print("MATCH_VALUE 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_MATCH_VALUE.source_code, "match_value_basic")
    
    # 运行测试
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_MATCH_VALUE, TEST_MATCH_STRING, TEST_MATCH_CONSTANTS]:
        success = test.run()
        print(test.get_report())
        print()
