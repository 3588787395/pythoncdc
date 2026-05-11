"""
测试状态: ⚠️ 部分
优先级: P2
相关任务: 已有基础支持，需要完善边界情况

描述:
    测试海象运算符 := 在各种场景下的使用

当前问题:
    - 复杂嵌套场景可能出错

期望输出:
    应正确输出 := 运算符
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 基本海象运算符
TEST_WALRUS_BASIC = DecompileTestCase(
    name="walrus_basic",
    source_code='''
if (n := len(data)) > 10:
    print(f"Long list: {n}")
'''.strip(),
    expected_patterns=["if (n := len(data)) > 10:", "print"]
)

# 测试用例2: while循环中的海象运算符
TEST_WALRUS_WHILE = DecompileTestCase(
    name="walrus_while",
    source_code='''
while (line := input()) != "quit":
    process(line)
'''.strip(),
    expected_patterns=["while (line := input()) != \"quit\":"]
)

# 测试用例3: 列表推导式中的海象运算符
TEST_WALRUS_COMPREHENSION = DecompileTestCase(
    name="walrus_comprehension",
    source_code='''
results = [y for x in data if (y := f(x)) > 0]
'''.strip(),
    expected_patterns=["[y for x in data if (y := f(x)) > 0]"]
)

# 测试用例4: 多重海象运算符
TEST_WALRUS_MULTIPLE = DecompileTestCase(
    name="walrus_multiple",
    source_code='''
if (a := 1) and (b := 2):
    print(a + b)
'''.strip(),
    expected_patterns=["if (a := 1) and (b := 2):"]
)

# 测试用例5: 嵌套海象运算符
TEST_WALRUS_NESTED = DecompileTestCase(
    name="walrus_nested",
    source_code='''
if (x := (y := 1) + 1) > 0:
    print(x, y)
'''.strip(),
    expected_patterns=["if (x := (y := 1) + 1) > 0:"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("海象运算符字节码示例")
    print("=" * 60)
    disassemble_code(TEST_WALRUS_BASIC.source_code, "walrus_basic")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_WALRUS_BASIC, TEST_WALRUS_WHILE, TEST_WALRUS_COMPREHENSION,
                 TEST_WALRUS_MULTIPLE, TEST_WALRUS_NESTED]:
        success = test.run()
        print(test.get_report())
        print()
