# Source Generated with Decompyle++ (Python version)
# File: test_async_generator.cpython-311.pyc (Python 3.11)

__doc__ = '\n测试异步生成器的反编译\n\n测试状态: 🔄 待验证\n优先级: P1\n\n描述:\n    测试异步生成器（async def ... yield）的正确反编译\n\n期望输出:\n    - 正确识别异步生成器函数\n    - yield语句正确生成\n    - await和yield混合正确处理\n'
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary
TEST_ASYNC_GEN_SIMPLE = AsyncTestCase(name='async_gen_simple', source_code='\nasync def simple_gen():\n    yield 1\n    yield 2\n    yield 3\n'.strip(), expected_patterns=['async def', 'yield 1', 'yield 2', 'yield 3'])
TEST_ASYNC_GEN_WITH_AWAIT = AsyncTestCase(name='async_gen_with_await', source_code='\nasync def async_range(n):\n    for i in range(n):\n        await asyncio.sleep(0.01)\n        yield i\n'.strip(), expected_patterns=['async def', 'await', 'yield i'])
TEST_ASYNC_GEN_CONDITIONAL = AsyncTestCase(name='async_gen_conditional', source_code='\nasync def filtered_gen(items):\n    async for item in items:\n        if item > 0:\n            yield item\n'.strip(), expected_patterns=['async def', 'async for', 'if item > 0', 'yield item'])
TEST_ASYNC_GEN_YIELD_FROM = AsyncTestCase(name='async_gen_yield_from', source_code='\nasync def combined_gen():\n    yield 1\n    yield 2\n    async for item in sub_gen():\n        yield item\n    yield 5\n'.strip(), expected_patterns=['async def', 'yield 1', 'async for', 'yield item', 'yield 5'])
TEST_ASYNC_GEN_NESTED = AsyncTestCase(name='async_gen_nested', source_code='\nasync def outer_gen():\n    async def inner_gen():\n        yield "inner"\n    \n    yield "outer start"\n    async for item in inner_gen():\n        yield item\n    yield "outer end"\n'.strip(), expected_patterns=['async def outer_gen', 'async def inner_gen', 'yield', 'async for'])
TEST_ASYNC_GEN_TRY_EXCEPT = AsyncTestCase(name='async_gen_try_except', source_code='\nasync def safe_gen():\n    try:\n        yield await fetch_item()\n    except Exception:\n        yield None\n'.strip(), expected_patterns=['async def', 'try:', 'except', 'yield await', 'yield None'])
if __name__ == '__main__':
    pass
test_cases = [TEST_ASYNC_GEN_SIMPLE, TEST_ASYNC_GEN_WITH_AWAIT, TEST_ASYNC_GEN_CONDITIONAL, TEST_ASYNC_GEN_YIELD_FROM, TEST_ASYNC_GEN_NESTED, TEST_ASYNC_GEN_TRY_EXCEPT]
results = run_test_suite(test_cases)
for detail in results['details']:
    print('\n' + detail['report'])
else:
    print_test_summary(results)
