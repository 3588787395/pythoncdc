# Source Generated with Decompyle++ (Python version)
# File: test_async_context.cpython-311.pyc (Python 3.11)

__doc__ = '\n测试异步上下文管理器的反编译\n\n测试状态: 🔄 待验证\n优先级: P1\n\n描述:\n    测试异步上下文管理器类（__aenter__, __aexit__）的正确反编译\n\n期望输出:\n    - 类定义正确\n    - __aenter__和__aexit__方法正确识别\n    - async with使用该类的语句正确\n'
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary
TEST_ASYNC_CONTEXT_BASIC = AsyncTestCase(name='async_context_basic', source_code='\nclass AsyncContext:\n    async def __aenter__(self):\n        await self.setup()\n        return self\n    \n    async def __aexit__(self, exc_type, exc_val, exc_tb):\n        await self.cleanup()\n'.strip(), expected_patterns=['class AsyncContext', 'async def __aenter__', 'async def __aexit__', 'await'])
TEST_ASYNC_CONTEXT_PARAMS = AsyncTestCase(name='async_context_params', source_code='\nclass AsyncConnection:\n    def __init__(self, host, port):\n        self.host = host\n        self.port = port\n    \n    async def __aenter__(self):\n        self.conn = await connect(self.host, self.port)\n        return self.conn\n    \n    async def __aexit__(self, exc_type, exc_val, exc_tb):\n        await self.conn.close()\n'.strip(), expected_patterns=['class AsyncConnection', 'def __init__', 'async def __aenter__', 'await connect'])
TEST_USE_ASYNC_CONTEXT = AsyncTestCase(name='use_async_context', source_code='\nasync def process_with_context():\n    async with AsyncContext() as ctx:\n        result = await ctx.do_work()\n        return result\n'.strip(), expected_patterns=['async def', 'async with', 'await ctx.do_work()'])
TEST_CONTEXT_WITH_EXCEPTION = AsyncTestCase(name='context_with_exception', source_code='\nclass Transaction:\n    async def __aenter__(self):\n        await self.begin()\n        return self\n    \n    async def __aexit__(self, exc_type, exc_val, exc_tb):\n        if exc_type is None:\n            await self.commit()\n        else:\n            await self.rollback()\n\nasync def do_transaction():\n    async with Transaction() as tx:\n        await tx.execute()\n'.strip(), expected_patterns=['class Transaction', 'async def __aenter__', 'async def __aexit__', 'if exc_type', 'async with'])
TEST_NESTED_CONTEXT_CLASS = AsyncTestCase(name='nested_context_class', source_code='\nclass OuterContext:\n    async def __aenter__(self):\n        async def setup():\n            await asyncio.sleep(0.01)\n            return "setup"\n        self.value = await setup()\n        return self\n    \n    async def __aexit__(self, exc_type, exc_val, exc_tb):\n        async def cleanup():\n            await asyncio.sleep(0.01)\n        await cleanup()\n'.strip(), expected_patterns=['class OuterContext', 'async def __aenter__', 'async def setup', 'await setup()'])
if __name__ == '__main__':
    pass
test_cases = [TEST_ASYNC_CONTEXT_BASIC, TEST_ASYNC_CONTEXT_PARAMS, TEST_USE_ASYNC_CONTEXT, TEST_CONTEXT_WITH_EXCEPTION, TEST_NESTED_CONTEXT_CLASS]
results = run_test_suite(test_cases)
for detail in results['details']:
    print('\n' + detail['report'])
else:
    print_test_summary(results)
