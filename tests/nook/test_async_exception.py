"""
测试异步异常处理的反编译

测试状态: 🔄 待验证
优先级: P1

描述:
    测试异步函数中try-except-finally的正确反编译

期望输出:
    - try-except结构完整
    - await在异常处理中正确保留
    - finally块正确处理
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary


# 测试用例1: 基本try-except
TEST_ASYNC_TRY_EXCEPT = AsyncTestCase(
    name="async_try_except",
    source_code='''
async def safe_operation():
    try:
        result = await risky_call()
        return result
    except Exception as e:
        await log_error(e)
        return None
'''.strip(),
    expected_patterns=["async def", "try:", "await risky_call()", "except", "await log_error"]
)

# 测试用例2: try-except-finally
TEST_ASYNC_TRY_FINALLY = AsyncTestCase(
    name="async_try_finally",
    source_code='''
async def with_cleanup():
    try:
        return await process()
    finally:
        await cleanup()
'''.strip(),
    expected_patterns=["async def", "try:", "await process()", "finally:", "await cleanup()"]
)

# 测试用例3: 多except子句
TEST_ASYNC_MULTI_EXCEPT = AsyncTestCase(
    name="async_multi_except",
    source_code='''
async def handle_errors():
    try:
        await operation()
    except ValueError as e:
        await handle_value_error(e)
    except TypeError as e:
        await handle_type_error(e)
    except Exception as e:
        await handle_generic(e)
'''.strip(),
    expected_patterns=["except ValueError", "except TypeError", "except Exception", "await"]
)

# 测试用例4: try-except-else-finally
TEST_ASYNC_COMPLETE = AsyncTestCase(
    name="async_complete",
    source_code='''
async def complete_handling():
    try:
        result = await main_op()
    except Exception as e:
        await handle_error(e)
        return None
    else:
        await on_success(result)
        return result
    finally:
        await always_run()
'''.strip(),
    expected_patterns=["try:", "except", "else:", "finally:", "await"]
)

# 测试用例5: 嵌套try-except
TEST_ASYNC_NESTED_TRY = AsyncTestCase(
    name="async_nested_try",
    source_code='''
async def nested_handling():
    try:
        outer = await outer_op()
        try:
            inner = await inner_op(outer)
            return inner
        except InnerError as e:
            await handle_inner(e)
    except OuterError as e:
        await handle_outer(e)
'''.strip(),
    expected_patterns=["try:", "except InnerError", "except OuterError", "await"]
)

# 测试用例6: async with中的异常处理
TEST_ASYNC_WITH_EXCEPT = AsyncTestCase(
    name="async_with_except",
    source_code='''
async def transaction_with_error():
    async with transaction() as tx:
        try:
            await tx.execute()
        except Exception:
            await tx.rollback()
            raise
'''.strip(),
    expected_patterns=["async with", "try:", "except", "await", "raise"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("异步异常处理测试")
    print("=" * 60)
    
    test_cases = [
        TEST_ASYNC_TRY_EXCEPT,
        TEST_ASYNC_TRY_FINALLY,
        TEST_ASYNC_MULTI_EXCEPT,
        TEST_ASYNC_COMPLETE,
        TEST_ASYNC_NESTED_TRY,
        TEST_ASYNC_WITH_EXCEPT,
    ]
    
    results = run_test_suite(test_cases)
    
    for detail in results['details']:
        print("\n" + detail['report'])
    
    print_test_summary(results)
