"""
测试状态: ⚠️ 部分
优先级: P1
相关任务: 任务3.2

描述:
    测试嵌套循环 + 异常处理交互

当前问题:
    - break/continue 在嵌套循环中可能指向错误的循环

期望输出:
    应正确识别循环层级关系
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 嵌套for循环
TEST_NESTED_FOR = DecompileTestCase(
    name="nested_for",
    source_code='''
for i in range(3):
    for j in range(3):
        print(i, j)
'''.strip(),
    expected_patterns=["for i in", "for j in", "print"]
)

# 测试用例2: 嵌套while循环
TEST_NESTED_WHILE = DecompileTestCase(
    name="nested_while",
    source_code='''
i = 0
while i < 3:
    j = 0
    while j < 3:
        print(i, j)
        j += 1
    i += 1
'''.strip(),
    expected_patterns=["while i < 3:", "while j < 3:", "print"]
)

# 测试用例3: for+while混合嵌套
TEST_MIXED_NESTED = DecompileTestCase(
    name="mixed_nested",
    source_code='''
for item in items:
    while item.processing():
        item.step()
'''.strip(),
    expected_patterns=["for item in", "while item.processing()"]
)

# 测试用例4: 嵌套循环中的break
TEST_NESTED_BREAK = DecompileTestCase(
    name="nested_break",
    source_code='''
for i in range(10):
    for j in range(10):
        if i == j:
            break
    print(i)
'''.strip(),
    expected_patterns=["for i in", "for j in", "if i == j:", "break", "print"]
)

# 测试用例5: 嵌套循环中的continue
TEST_NESTED_CONTINUE = DecompileTestCase(
    name="nested_continue",
    source_code='''
for i in range(10):
    for j in range(10):
        if j % 2 == 0:
            continue
        print(i, j)
'''.strip(),
    expected_patterns=["for i in", "for j in", "if j % 2 == 0:", "continue"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("嵌套循环字节码示例")
    print("=" * 60)
    disassemble_code(TEST_NESTED_FOR.source_code, "nested_for")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_NESTED_FOR, TEST_NESTED_WHILE, TEST_MIXED_NESTED, 
                 TEST_NESTED_BREAK, TEST_NESTED_CONTINUE]:
        success = test.run()
        print(test.get_report())
        print()
