# Source Generated with Decompyle++ (Python version)
# File: test_async_for.cpython-311.pyc (Python 3.11)

__doc__ = '\n测试异步for循环的反编译\n\n测试状态: 🔄 待验证\n优先级: P0\n\n描述:\n    测试async for循环的正确识别和反编译\n\n期望输出:\n    - 正确包含async for关键字\n    - 循环变量和迭代对象正确\n    - 循环体完整\n'
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary
TEST_ASYNC_FOR_BASIC = AsyncTestCase(name='async_for_basic', source_code='\nasync def process_items():\n    async for item in async_generator():\n        print(item)\n'.strip(), expected_patterns=['async def', 'async for', 'in async_generator()', 'print(item)'])
TEST_ASYNC_FOR_ELSE = AsyncTestCase(name='async_for_else', source_code='\nasync def search():\n    async for item in items:\n        if item.found:\n            return item\n    else:\n        return None\n'.strip(), expected_patterns=['async for', 'else:', 'return None'])
TEST_ASYNC_FOR_NESTED = AsyncTestCase(name='async_for_nested', source_code='\nasync def nested():\n    async for outer in outer_iter():\n        async for inner in inner_iter(outer):\n            process(inner)\n'.strip(), expected_patterns=['async for outer', 'async for inner', 'process'])
TEST_ASYNC_FOR_CONTROL = AsyncTestCase(name='async_for_control', source_code='\nasync def control_flow():\n    async for item in items:\n        if item.skip:\n            continue\n        if item.stop:\n            break\n        process(item)\n'.strip(), expected_patterns=['async for', 'continue', 'break', 'process'])
TEST_ASYNC_FOR_TARGET = AsyncTestCase(name='async_for_target', source_code='\nasync def unpack_items():\n    async for key, value in async_items():\n        store(key, value)\n    \n    async for [a, b, c] in async_lists():\n        process(a, b, c)\n'.strip(), expected_patterns=['async for', 'key, value', '[a, b, c]'])
if __name__ == '__main__':
    pass
test_cases = [TEST_ASYNC_FOR_BASIC, TEST_ASYNC_FOR_ELSE, TEST_ASYNC_FOR_NESTED, TEST_ASYNC_FOR_CONTROL, TEST_ASYNC_FOR_TARGET]
results = run_test_suite(test_cases)
for detail in results['details']:
    print('\n' + detail['report'])
else:
    print_test_summary(results)
