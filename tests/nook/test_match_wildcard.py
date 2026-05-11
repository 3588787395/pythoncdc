"""
测试状态: ❌ 失败
优先级: P0
相关任务: 任务1.1

描述:
    测试 match/case 中的通配符模式
    case _ 应该匹配任何值

当前问题:
    - 不支持通配符模式

期望输出:
    应正确输出 case _: 结构
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 基本通配符
TEST_WILDCARD_BASIC = DecompileTestCase(
    name="match_wildcard_basic",
    source_code='''
x = 42
match x:
    case 1:
        result = "one"
    case _:
        result = "other"
'''.strip(),
    expected_patterns=["match", "case 1:", "case _:", "result"]
)

# 测试用例2: 只有通配符
TEST_WILDCARD_ONLY = DecompileTestCase(
    name="match_wildcard_only",
    source_code='''
match value:
    case _:
        print("matched anything")
'''.strip(),
    expected_patterns=["match", "case _:", "print"]
)

# 测试用例3: 通配符在多个case之后
TEST_WILDCARD_LAST = DecompileTestCase(
    name="match_wildcard_last",
    source_code='''
match status:
    case 200:
        msg = "OK"
    case 404:
        msg = "Not Found"
    case 500:
        msg = "Error"
    case _:
        msg = "Unknown"
'''.strip(),
    expected_patterns=["match", "case 200:", "case 404:", "case 500:", "case _:"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("MATCH 通配符模式字节码示例")
    print("=" * 60)
    disassemble_code(TEST_WILDCARD_BASIC.source_code, "match_wildcard_basic")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_WILDCARD_BASIC, TEST_WILDCARD_ONLY, TEST_WILDCARD_LAST]:
        success = test.run()
        print(test.get_report())
        print()
