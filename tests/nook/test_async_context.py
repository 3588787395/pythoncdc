"""
测试异步上下文管理器的反编译

测试状态: 🔄 待验证
优先级: P1

描述:
    测试异步上下文管理器类（__aenter__, __aexit__）的正确反编译

期望输出:
    - 类定义正确
    - __aenter__和__aexit__方法正确识别
    - async with使用该类的语句正确
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary


# 测试用例1: 基本异步上下文管理器
TEST_ASYNC_CONTEXT_BASIC = AsyncTestCase(
    name="async_context_basic",
    source_code='''
class AsyncContext:
    async def __aenter__(self):
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
'''.strip(),
    expected_patterns=["class AsyncContext", "async def __aenter__", "async def __aexit__", "await"]
)

# 测试用例2: 带参数的异步上下文管理器
TEST_ASYNC_CONTEXT_PARAMS = AsyncTestCase(
    name="async_context_params",
    source_code='''
class AsyncConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
    
    async def __aenter__(self):
        self.conn = await connect(self.host, self.port)
        return self.conn
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.conn.close()
'''.strip(),
    expected_patterns=["class AsyncConnection", "def __init__", "async def __aenter__", "await connect"]
)

# 测试用例3: 使用异步上下文管理器
TEST_USE_ASYNC_CONTEXT = AsyncTestCase(
    name="use_async_context",
    source_code='''
async def process_with_context():
    async with AsyncContext() as ctx:
        result = await ctx.do_work()
        return result
'''.strip(),
    expected_patterns=["async def", "async with", "await ctx.do_work()"]
)

# 测试用例4: 异步上下文管理器with异常处理
TEST_CONTEXT_WITH_EXCEPTION = AsyncTestCase(
    name="context_with_exception",
    source_code='''
class Transaction:
    async def __aenter__(self):
        await self.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

async def do_transaction():
    async with Transaction() as tx:
        await tx.execute()
'''.strip(),
    expected_patterns=["class Transaction", "async def __aenter__", "async def __aexit__", "if exc_type", "async with"]
)

# 测试用例5: 嵌套异步上下文管理器类
TEST_NESTED_CONTEXT_CLASS = AsyncTestCase(
    name="nested_context_class",
    source_code='''
class OuterContext:
    async def __aenter__(self):
        async def setup():
            await asyncio.sleep(0.01)
            return "setup"
        self.value = await setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async def cleanup():
            await asyncio.sleep(0.01)
        await cleanup()
'''.strip(),
    expected_patterns=["class OuterContext", "async def __aenter__", "async def setup", "await setup()"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("异步上下文管理器测试")
    print("=" * 60)
    
    test_cases = [
        TEST_ASYNC_CONTEXT_BASIC,
        TEST_ASYNC_CONTEXT_PARAMS,
        TEST_USE_ASYNC_CONTEXT,
        TEST_CONTEXT_WITH_EXCEPTION,
        TEST_NESTED_CONTEXT_CLASS,
    ]
    
    results = run_test_suite(test_cases)
    
    for detail in results['details']:
        print("\n" + detail['report'])
    
    print_test_summary(results)
