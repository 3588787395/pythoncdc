"""
测试简单异步函数定义的反编译

测试状态: 🔄 待验证
优先级: P0

描述:
    测试简单async def函数的正确反编译

期望输出:
    - 正确包含async def关键字
    - 函数体完整保留
    - 语法正确
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary


# 测试用例1: 最简单的异步函数
TEST_SIMPLE_ASYNC_DEF = AsyncTestCase(
    name="simple_async_def",
    source_code='''
async def simple():
    return 42
'''.strip(),
    expected_patterns=["async def", "return 42"]
)

# 测试用例2: 带参数的异步函数
TEST_ASYNC_WITH_PARAMS = AsyncTestCase(
    name="async_with_params",
    source_code='''
async def greet(name, message="Hello"):
    result = f"{message}, {name}!"
    return result
'''.strip(),
    expected_patterns=["async def", "name", "message", "return result"]
)

# 测试用例3: 异步函数调用异步函数
TEST_ASYNC_CALL_ASYNC = AsyncTestCase(
    name="async_call_async",
    source_code='''
async def inner():
    return "inner result"

async def outer():
    result = await inner()
    return result
'''.strip(),
    expected_patterns=["async def inner", "async def outer", "await inner()", "return result"]
)

# 测试用例4: 多个异步函数
TEST_MULTIPLE_ASYNC = AsyncTestCase(
    name="multiple_async",
    source_code='''
async def func1():
    return 1

async def func2():
    return 2

async def func3():
    x = await func1()
    y = await func2()
    return x + y
'''.strip(),
    expected_patterns=["async def func1", "async def func2", "async def func3", "await func1()", "await func2()"]
)

# 测试用例5: 异步函数与普通函数混合
TEST_MIXED_FUNCTIONS = AsyncTestCase(
    name="mixed_functions",
    source_code='''
def sync_func():
    return "sync"

async def async_func():
    return "async"

def another_sync():
    return sync_func()

async def another_async():
    return await async_func()
'''.strip(),
    expected_patterns=[
        "def sync_func",
        "async def async_func",
        "def another_sync",
        "async def another_async",
        "await async_func()"
    ]
)


if __name__ == "__main__":
    print("=" * 60)
    print("简单异步函数定义测试")
    print("=" * 60)
    
    test_cases = [
        TEST_SIMPLE_ASYNC_DEF,
        TEST_ASYNC_WITH_PARAMS,
        TEST_ASYNC_CALL_ASYNC,
        TEST_MULTIPLE_ASYNC,
        TEST_MIXED_FUNCTIONS,
    ]
    
    results = run_test_suite(test_cases)
    
    # 打印详细报告
    for detail in results['details']:
        print("\n" + detail['report'])
    
    print_test_summary(results)
