# Source Generated with Decompyle++ (Python version)
# File: test_async_await.cpython-311.pyc (Python 3.11)

__doc__ = '\n测试await表达式的反编译\n\n测试状态: 🔄 待验证\n优先级: P0\n\n描述:\n    测试await表达式的正确反编译\n\n期望输出:\n    - 正确包含await关键字\n    - 等待的表达式正确\n    - 各种await场景正确处理\n'
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary
TEST_AWAIT_SIMPLE = AsyncTestCase(name='await_simple', source_code='\nasync def simple_await():\n    result = await fetch_data()\n    return result\n'.strip(), expected_patterns=['async def', 'await fetch_data()', 'return result'])
TEST_AWAIT_IN_EXPR = AsyncTestCase(name='await_in_expr', source_code='\nasync def expr_await():\n    x = await get_x()\n    y = await get_y()\n    return x + y\n'.strip(), expected_patterns=['await get_x()', 'await get_y()', 'return x + y'])
TEST_AWAIT_METHOD = AsyncTestCase(name='await_method', source_code='\nasync def method_await(obj):\n    result = await obj.process()\n    return result\n'.strip(), expected_patterns=['await obj.process()'])
TEST_AWAIT_WITH_ARGS = AsyncTestCase(name='await_with_args', source_code='\nasync def args_await():\n    result = await call(a, b, key=value)\n    return result\n'.strip(), expected_patterns=['await call(a, b, key=value)'])
TEST_AWAIT_SEQUENCE = AsyncTestCase(name='await_sequence', source_code='\nasync def sequence_await():\n    step1 = await step_one()\n    step2 = await step_two(step1)\n    step3 = await step_three(step2)\n    return step3\n'.strip(), expected_patterns=['await step_one()', 'await step_two', 'await step_three'])
TEST_AWAIT_IN_CONDITION = AsyncTestCase(name='await_in_condition', source_code='\nasync def condition_await():\n    if await check_condition():\n        return True\n    return False\n'.strip(), expected_patterns=['await check_condition()', 'if', 'return True'])
TEST_AWAIT_IN_RETURN = AsyncTestCase(name='await_in_return', source_code='\nasync def return_await():\n    return await compute_result()\n'.strip(), expected_patterns=['return await compute_result()'])
if __name__ == '__main__':
    pass
test_cases = [TEST_AWAIT_SIMPLE, TEST_AWAIT_IN_EXPR, TEST_AWAIT_METHOD, TEST_AWAIT_WITH_ARGS, TEST_AWAIT_SEQUENCE, TEST_AWAIT_IN_CONDITION, TEST_AWAIT_IN_RETURN]
results = run_test_suite(test_cases)
for detail in results['details']:
    print('\n' + detail['report'])
else:
    print_test_summary(results)
