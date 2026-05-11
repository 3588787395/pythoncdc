# Source Generated with Decompyle++ (Python version)
# File: test_async_with_2.cpython-311.pyc (Python 3.11)

__doc__ = '\n测试异步with语句的反编译\n\n测试状态: 🔄 待验证\n优先级: P0\n\n描述:\n    测试async with语句的正确识别和反编译\n\n期望输出:\n    - 正确包含async with关键字\n    - 上下文管理器表达式正确\n    - as子句正确处理\n'
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary
TEST_ASYNC_WITH_BASIC = AsyncTestCase(name='async_with_basic', source_code='\nasync def use_context():\n    async with get_context() as ctx:\n        await ctx.process()\n'.strip(), expected_patterns=['async def', 'async with', 'await', 'ctx.process()'])
TEST_ASYNC_WITH_NO_AS = AsyncTestCase(name='async_with_no_as', source_code='\nasync def simple_context():\n    async with lock:\n        await critical_section()\n'.strip(), expected_patterns=['async with', 'lock', 'await'])
TEST_ASYNC_WITH_NESTED = AsyncTestCase(name='async_with_nested', source_code='\nasync def nested_contexts():\n    async with outer_ctx() as outer:\n        async with inner_ctx() as inner:\n            result = await outer.combine(inner)\n            return result\n'.strip(), expected_patterns=['async with outer_ctx', 'async with inner_ctx', 'await'])
TEST_ASYNC_WITH_MULTIPLE = AsyncTestCase(name='async_with_multiple', source_code='\nasync def multiple_contexts():\n    async with ctx1() as a, ctx2() as b, ctx3() as c:\n        return await process(a, b, c)\n'.strip(), expected_patterns=['async with', 'ctx1()', 'ctx2()', 'ctx3()', 'await'])
TEST_ASYNC_WITH_EXCEPTION = AsyncTestCase(name='async_with_exception', source_code='\nasync def safe_context():\n    async with transaction() as tx:\n        try:\n            await tx.execute()\n        except Exception as e:\n            await tx.rollback()\n            raise\n'.strip(), expected_patterns=['async with', 'try:', 'except', 'await'])
if __name__ == '__main__':
    pass
test_cases = [TEST_ASYNC_WITH_BASIC, TEST_ASYNC_WITH_NO_AS, TEST_ASYNC_WITH_NESTED, TEST_ASYNC_WITH_MULTIPLE, TEST_ASYNC_WITH_EXCEPTION]
results = run_test_suite(test_cases)
for detail in results['details']:
    print('\n' + detail['report'])
else:
    print_test_summary(results)
