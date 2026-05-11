"""
测试异步with语句的反编译

测试状态: 🔄 待验证
优先级: P0

描述:
    测试async with语句的正确识别和反编译

期望输出:
    - 正确包含async with关键字
    - 上下文管理器表达式正确
    - as子句正确处理
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary


# 测试用例1: 基本async with
TEST_ASYNC_WITH_BASIC = AsyncTestCase(
    name="async_with_basic",
    source_code='''
async def use_context():
    async with get_context() as ctx:
        await ctx.process()
'''.strip(),
    expected_patterns=["async def", "async with", "await", "ctx.process()"]
)

# 测试用例2: async without as
TEST_ASYNC_WITH_NO_AS = AsyncTestCase(
    name="async_with_no_as",
    source_code='''
async def simple_context():
    async with lock:
        await critical_section()
'''.strip(),
    expected_patterns=["async with", "lock", "await"]
)

# 测试用例3: 嵌套async with
TEST_ASYNC_WITH_NESTED = AsyncTestCase(
    name="async_with_nested",
    source_code='''
async def nested_contexts():
    async with outer_ctx() as outer:
        async with inner_ctx() as inner:
            result = await outer.combine(inner)
            return result
'''.strip(),
    expected_patterns=["async with outer_ctx", "async with inner_ctx", "await"]
)

# 测试用例4: 多上下文async with
TEST_ASYNC_WITH_MULTIPLE = AsyncTestCase(
    name="async_with_multiple",
    source_code='''
async def multiple_contexts():
    async with ctx1() as a, ctx2() as b, ctx3() as c:
        return await process(a, b, c)
'''.strip(),
    expected_patterns=["async with", "ctx1()", "ctx2()", "ctx3()", "await"]
)

# 测试用例5: async with与异常处理
TEST_ASYNC_WITH_EXCEPTION = AsyncTestCase(
    name="async_with_exception",
    source_code='''
async def safe_context():
    async with transaction() as tx:
        try:
            await tx.execute()
        except Exception as e:
            await tx.rollback()
            raise
'''.strip(),
    expected_patterns=["async with", "try:", "except", "await"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("异步with语句测试")
    print("=" * 60)
    
    test_cases = [
        TEST_ASYNC_WITH_BASIC,
        TEST_ASYNC_WITH_NO_AS,
        TEST_ASYNC_WITH_NESTED,
        TEST_ASYNC_WITH_MULTIPLE,
        TEST_ASYNC_WITH_EXCEPTION,
    ]
    
    results = run_test_suite(test_cases)
    
    for detail in results['details']:
        print("\n" + detail['report'])
    
    print_test_summary(results)
