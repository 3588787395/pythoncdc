"""
测试异步for循环的反编译

测试状态: 🔄 待验证
优先级: P0

描述:
    测试async for循环的正确识别和反编译

期望输出:
    - 正确包含async for关键字
    - 循环变量和迭代对象正确
    - 循环体完整
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary


# 测试用例1: 基本async for
TEST_ASYNC_FOR_BASIC = AsyncTestCase(
    name="async_for_basic",
    source_code='''
async def process_items():
    async for item in async_generator():
        print(item)
'''.strip(),
    expected_patterns=["async def", "async for", "in async_generator()", "print(item)"]
)

# 测试用例2: async for with else
TEST_ASYNC_FOR_ELSE = AsyncTestCase(
    name="async_for_else",
    source_code='''
async def search():
    async for item in items:
        if item.found:
            return item
    else:
        return None
'''.strip(),
    expected_patterns=["async for", "else:", "return None"]
)

# 测试用例3: 嵌套async for
TEST_ASYNC_FOR_NESTED = AsyncTestCase(
    name="async_for_nested",
    source_code='''
async def nested():
    async for outer in outer_iter():
        async for inner in inner_iter(outer):
            process(inner)
'''.strip(),
    expected_patterns=["async for outer", "async for inner", "process"]
)

# 测试用例4: async for with break/continue
TEST_ASYNC_FOR_CONTROL = AsyncTestCase(
    name="async_for_control",
    source_code='''
async def control_flow():
    async for item in items:
        if item.skip:
            continue
        if item.stop:
            break
        process(item)
'''.strip(),
    expected_patterns=["async for", "continue", "break", "process"]
)

# 测试用例5: async for with复杂循环变量
TEST_ASYNC_FOR_TARGET = AsyncTestCase(
    name="async_for_target",
    source_code='''
async def unpack_items():
    async for key, value in async_items():
        store(key, value)
    
    async for [a, b, c] in async_lists():
        process(a, b, c)
'''.strip(),
    expected_patterns=["async for", "key, value", "[a, b, c]"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("异步for循环测试")
    print("=" * 60)
    
    test_cases = [
        TEST_ASYNC_FOR_BASIC,
        TEST_ASYNC_FOR_ELSE,
        TEST_ASYNC_FOR_NESTED,
        TEST_ASYNC_FOR_CONTROL,
        TEST_ASYNC_FOR_TARGET,
    ]
    
    results = run_test_suite(test_cases)
    
    for detail in results['details']:
        print("\n" + detail['report'])
    
    print_test_summary(results)
