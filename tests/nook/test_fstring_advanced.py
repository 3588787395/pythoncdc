"""
测试状态: ⚠️ 部分
优先级: P2
相关任务: 已有基础支持，需要完善边界情况

描述:
    测试高级 f-string 特性

当前问题:
    - 复杂格式化表达式可能处理不正确

期望输出:
    应正确输出 f-string 语法
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 基本f-string
TEST_FSTRING_BASIC = DecompileTestCase(
    name="fstring_basic",
    source_code='''
name = "World"
message = f"Hello, {name}!"
'''.strip(),
    expected_patterns=['f"Hello, {name}!"']
)

# 测试用例2: f-string中的表达式
TEST_FSTRING_EXPRESSION = DecompileTestCase(
    name="fstring_expression",
    source_code='''
x = 10
y = 20
result = f"{x} + {y} = {x + y}"
'''.strip(),
    expected_patterns=['f"{x} + {y} = {x + y}"']
)

# 测试用例3: f-string格式化规范
TEST_FSTRING_FORMAT = DecompileTestCase(
    name="fstring_format",
    source_code='''
pi = 3.14159
formatted = f"Pi = {pi:.2f}"
number = 42
padded = f"Number: {number:05d}"
'''.strip(),
    expected_patterns=['f"Pi = {pi:.2f}"', 'f"Number: {number:05d}"']
)

# 测试用例4: 嵌套f-string
TEST_FSTRING_NESTED = DecompileTestCase(
    name="fstring_nested",
    source_code='''
width = 10
precision = 4
value = 12.34567
result = f"Result: {value:{width}.{precision}f}"
'''.strip(),
    expected_patterns=['f"Result: {value:{width}.{precision}f}"']
)

# 测试用例5: 多行f-string
TEST_FSTRING_MULTILINE = DecompileTestCase(
    name="fstring_multiline",
    source_code='''
name = "Alice"
age = 30
info = f"""
Name: {name}
Age: {age}
"""
'''.strip(),
    expected_patterns=['f"""', "Name: {name}", "Age: {age}"]
)

# 测试用例6: f-string中的引号转义
TEST_FSTRING_QUOTES = DecompileTestCase(
    name="fstring_quotes",
    source_code='''
name = "Bob"
message = f'Hello, "{name}"!'
'''.strip(),
    expected_patterns=['f\'Hello, "{name}"!\'']
)


if __name__ == "__main__":
    print("=" * 60)
    print("高级 f-string 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_FSTRING_BASIC.source_code, "fstring_basic")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_FSTRING_BASIC, TEST_FSTRING_EXPRESSION, TEST_FSTRING_FORMAT,
                 TEST_FSTRING_NESTED, TEST_FSTRING_MULTILINE, TEST_FSTRING_QUOTES]:
        success = test.run()
        print(test.get_report())
        print()
