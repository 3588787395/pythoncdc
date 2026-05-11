"""
测试异步生成器的反编译

测试状态: 🔄 待验证
优先级: P1

描述:
    测试异步生成器（async def ... yield）的正确反编译

期望输出:
    - 正确识别异步生成器函数
    - yield语句正确生成
    - await和yield混合正确处理
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary


# 测试用例1: 简单异步生成器
TEST_ASYNC_GEN_SIMPLE = AsyncTestCase(
    name="async_gen_simple",
    source_code='''
async def simple_gen():
    yield 1
    yield 2
    yield 3
'''.strip(),
    expected_patterns=["async def", "yield 1", "yield 2", "yield 3"]
)

# 测试用例2: 带await的异步生成器
TEST_ASYNC_GEN_WITH_AWAIT = AsyncTestCase(
    name="async_gen_with_await",
    source_code='''
async def async_range(n):
    for i in range(n):
        await asyncio.sleep(0.01)
        yield i
'''.strip(),
    expected_patterns=["async def", "await", "yield i"]
)

# 测试用例3: 异步生成器with条件
TEST_ASYNC_GEN_CONDITIONAL = AsyncTestCase(
    name="async_gen_conditional",
    source_code='''
async def filtered_gen(items):
    async for item in items:
        if item > 0:
            yield item
'''.strip(),
    expected_patterns=["async def", "async for", "if item > 0", "yield item"]
)

# 测试用例4: 异步生成器使用yield from
TEST_ASYNC_GEN_YIELD_FROM = AsyncTestCase(
    name="async_gen_yield_from",
    source_code='''
async def combined_gen():
    yield 1
    yield 2
    async for item in sub_gen():
        yield item
    yield 5
'''.strip(),
    expected_patterns=["async def", "yield 1", "async for", "yield item", "yield 5"]
)

# 测试用例5: 嵌套异步生成器
TEST_ASYNC_GEN_NESTED = AsyncTestCase(
    name="async_gen_nested",
    source_code='''
async def outer_gen():
    async def inner_gen():
        yield "inner"
    
    yield "outer start"
    async for item in inner_gen():
        yield item
    yield "outer end"
'''.strip(),
    expected_patterns=["async def outer_gen", "async def inner_gen", "yield", "async for"]
)

# 测试用例6: 异步生成器with try-except
TEST_ASYNC_GEN_TRY_EXCEPT = AsyncTestCase(
    name="async_gen_try_except",
    source_code='''
async def safe_gen():
    try:
        yield await fetch_item()
    except Exception:
        yield None
'''.strip(),
    expected_patterns=["async def", "try:", "except", "yield await", "yield None"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("异步生成器测试")
    print("=" * 60)
    
    test_cases = [
        TEST_ASYNC_GEN_SIMPLE,
        TEST_ASYNC_GEN_WITH_AWAIT,
        TEST_ASYNC_GEN_CONDITIONAL,
        TEST_ASYNC_GEN_YIELD_FROM,
        TEST_ASYNC_GEN_NESTED,
        TEST_ASYNC_GEN_TRY_EXCEPT,
    ]
    
    results = run_test_suite(test_cases)
    
    for detail in results['details']:
        print("\n" + detail['report'])
    
    print_test_summary(results)
