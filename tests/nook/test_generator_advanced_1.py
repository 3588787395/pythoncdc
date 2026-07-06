"""
测试状态: ❌ 失败
优先级: P2
相关任务: 任务2.3 / 生成器send支持

描述:
    测试高级生成器特性，包括 send() 和 throw()

当前问题:
    - yield from 在异步函数中可能出错
    - 生成器 send 表达式没有被正确提取

期望输出:
    应正确输出 yield 和 yield from 语法
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 基本生成器
TEST_GENERATOR_BASIC = DecompileTestCase(
    name="generator_basic",
    source_code='''
def count_up_to(n):
    i = 0
    while i < n:
        yield i
        i += 1
'''.strip(),
    expected_patterns=["def count_up_to(n):", "while i < n:", "yield i"]
)

# 测试用例2: 生成器send
TEST_GENERATOR_SEND = DecompileTestCase(
    name="generator_send",
    source_code='''
def accumulator():
    total = 0
    while True:
        value = yield total
        if value is None:
            break
        total += value
'''.strip(),
    expected_patterns=["def accumulator():", "while True:", "value = yield total"]
)

# 测试用例3: yield from
TEST_GENERATOR_YIELD_FROM = DecompileTestCase(
    name="generator_yield_from",
    source_code='''
def flatten(nested):
    for sublist in nested:
        yield from sublist
'''.strip(),
    expected_patterns=["def flatten(nested):", "for sublist in nested:", "yield from sublist"]
)

# 测试用例4: 嵌套生成器
TEST_GENERATOR_NESTED = DecompileTestCase(
    name="generator_nested",
    source_code='''
def outer():
    yield 1
    yield from inner()
    yield 4

def inner():
    yield 2
    yield 3
'''.strip(),
    expected_patterns=["def outer():", "yield 1", "yield from inner()", "yield 4"]
)

# 测试用例5: 生成器表达式
TEST_GENERATOR_EXPRESSION = DecompileTestCase(
    name="generator_expression",
    source_code='''
squares = (x*x for x in range(10))
evens = (x for x in range(20) if x % 2 == 0)
'''.strip(),
    expected_patterns=["(x*x for x in range(10))", "(x for x in range(20) if x % 2 == 0)"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("高级生成器字节码示例")
    print("=" * 60)
    disassemble_code(TEST_GENERATOR_BASIC.source_code, "generator_basic")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_GENERATOR_BASIC, TEST_GENERATOR_SEND, TEST_GENERATOR_YIELD_FROM,
                 TEST_GENERATOR_NESTED, TEST_GENERATOR_EXPRESSION]:
        success = test.run()
        print(test.get_report())
        print()
