"""
测试状态: ❌ 失败
优先级: P0
相关任务: 任务1.6, 1.7

描述:
    测试 match/case 的捕获模式 (MATCH_AS) 和守卫 (guard)
    使用 MATCH_AS 字节码指令

当前问题:
    - 完全不支持 MATCH_AS 指令
    - 无法识别 case [1, 2] as lst: 这样的捕获模式
    - 无法识别 case n if n < 13: 这样的守卫条件

期望输出:
    应包含 case [1, 2] as lst: 和 case n if n < 13: 这样的模式
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 捕获模式 (as)
TEST_MATCH_AS = DecompileTestCase(
    name="match_as",
    source_code='''
x = [1, 2, 3]

match x:
    case [1, 2] as lst:
        result = f"list: {lst}"
    case {"name": str(name)} as person:
        result = f"person: {person}"
    case _ as default:
        result = f"default: {default}"
'''.strip(),
    expected_patterns=["match", "case [1, 2] as lst:", "case _ as default:", "result"]
)

# 测试用例2: 守卫条件 (if)
TEST_MATCH_GUARD = DecompileTestCase(
    name="match_guard",
    source_code='''
age = 25

match age:
    case n if n < 13:
        category = "child"
    case n if n < 20:
        category = "teenager"
    case n if n < 65:
        category = "adult"
    case _:
        category = "senior"
'''.strip(),
    expected_patterns=["match", "case n if n < 13:", "case n if n < 20:", "category"]
)

# 测试用例3: 捕获 + 守卫组合
TEST_MATCH_AS_GUARD = DecompileTestCase(
    name="match_as_guard",
    source_code='''
values = [1, 2, 3, 4, 5]

match values:
    case [first, *rest] as lst if len(lst) > 3:
        result = f"long list: {lst}"
    case [first, *rest] as lst if len(lst) <= 3:
        result = f"short list: {lst}"
    case _:
        result = "other"
'''.strip(),
    expected_patterns=["match", "case [first, *rest] as lst if", "result"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("MATCH_AS / GUARD 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_MATCH_AS.source_code, "match_as")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_MATCH_AS, TEST_MATCH_GUARD, TEST_MATCH_AS_GUARD]:
        success = test.run()
        print(test.get_report())
        print()
