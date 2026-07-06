"""
测试await表达式的反编译

测试状态: 🔄 待验证
优先级: P0

描述:
    测试await表达式的正确反编译

期望输出:
    - 正确包含await关键字
    - 等待的表达式正确
    - 各种await场景正确处理
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary


# 测试用例1: 简单await
TEST_AWAIT_SIMPLE = AsyncTestCase(
    name="await_simple",
    source_code='''
async def simple_await():
    result = await fetch_data()
    return result
'''.strip(),
    expected_patterns=["async def", "await fetch_data()", "return result"]
)

# 测试用例2: await在表达式中
TEST_AWAIT_IN_EXPR = AsyncTestCase(
    name="await_in_expr",
    source_code='''
async def expr_await():
    x = await get_x()
    y = await get_y()
    return x + y
'''.strip(),
    expected_patterns=["await get_x()", "await get_y()", "return x + y"]
)

# 测试用例3: await方法调用
TEST_AWAIT_METHOD = AsyncTestCase(
    name="await_method",
    source_code='''
async def method_await(obj):
    result = await obj.process()
    return result
'''.strip(),
    expected_patterns=["await obj.process()"]
)

# 测试用例4: await带参数
TEST_AWAIT_WITH_ARGS = AsyncTestCase(
    name="await_with_args",
    source_code='''
async def args_await():
    result = await call(a, b, key=value)
    return result
'''.strip(),
    expected_patterns=["await call(a, b, key=value)"]
)

# 测试用例5: 多个await顺序执行
TEST_AWAIT_SEQUENCE = AsyncTestCase(
    name="await_sequence",
    source_code='''
async def sequence_await():
    step1 = await step_one()
    step2 = await step_two(step1)
    step3 = await step_three(step2)
    return step3
'''.strip(),
    expected_patterns=["await step_one()", "await step_two", "await step_three"]
)

# 测试用例6: await在条件中
TEST_AWAIT_IN_CONDITION = AsyncTestCase(
    name="await_in_condition",
    source_code='''
async def condition_await():
    if await check_condition():
        return True
    return False
'''.strip(),
    expected_patterns=["await check_condition()", "if", "return True"]
)

# 测试用例7: await在return中
TEST_AWAIT_IN_RETURN = AsyncTestCase(
    name="await_in_return",
    source_code='''
async def return_await():
    return await compute_result()
'''.strip(),
    expected_patterns=["return await compute_result()"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("Await表达式测试")
    print("=" * 60)
    
    test_cases = [
        TEST_AWAIT_SIMPLE,
        TEST_AWAIT_IN_EXPR,
        TEST_AWAIT_METHOD,
        TEST_AWAIT_WITH_ARGS,
        TEST_AWAIT_SEQUENCE,
        TEST_AWAIT_IN_CONDITION,
        TEST_AWAIT_IN_RETURN,
    ]
    
    results = run_test_suite(test_cases)
    
    for detail in results['details']:
        print("\n" + detail['report'])
    
    print_test_summary(results)
