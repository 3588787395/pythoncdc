# Source Generated with Decompyle++ (Python version)
# File: test_async_comprehension.cpython-311.pyc (Python 3.11)

__doc__ = '\n测试异步推导式的反编译\n\n测试状态: 🔄 待验证\n优先级: P1\n\n描述:\n    测试异步推导式（[x async for x in iter]）的正确反编译\n\n期望输出:\n    - 正确包含async for关键字在推导式中\n    - 列表、字典、集合推导式都支持\n    - 带条件的异步推导式正确处理\n'
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary
TEST_ASYNC_COMP_LIST = AsyncTestCase(name='async_comp_list', source_code='\nasync def get_results():\n    return [x async for x in async_iter()]\n'.strip(), expected_patterns=['async def', 'async for', 'async_iter'])
TEST_ASYNC_COMP_DICT = AsyncTestCase(name='async_comp_dict', source_code='\nasync def get_mapping():\n    return {k: v async for k, v in async_items()}\n'.strip(), expected_patterns=['async def', 'async for', 'async_items'])
TEST_ASYNC_COMP_SET = AsyncTestCase(name='async_comp_set', source_code='\nasync def get_unique():\n    return {x async for x in async_iter()}\n'.strip(), expected_patterns=['async def', 'async for'])
TEST_ASYNC_COMP_FILTER = AsyncTestCase(name='async_comp_filter', source_code='\nasync def get_filtered():\n    return [x async for x in async_iter() if x > 0]\n'.strip(), expected_patterns=['async for', 'if x > 0'])
TEST_ASYNC_COMP_NESTED = AsyncTestCase(name='async_comp_nested', source_code='\nasync def get_nested():\n    return [y async for x in outer_iter() async for y in inner_iter(x)]\n'.strip(), expected_patterns=['async for x', 'async for y'])
TEST_ASYNC_COMP_GENERATOR = AsyncTestCase(name='async_comp_generator', source_code='\nasync def get_gen():\n    return (x * 2 async for x in async_iter())\n'.strip(), expected_patterns=['async def', 'async for'])
TEST_ASYNC_COMP_MIXED = AsyncTestCase(name='async_comp_mixed', source_code='\nasync def process():\n    # 列表推导式包含异步生成器\n    items = [x async for x in async_gen()]\n    # 普通列表推导式处理结果\n    doubled = [x * 2 for x in items]\n    return doubled\n'.strip(), expected_patterns=['async for', 'for x in items'])
if __name__ == '__main__':
    pass
test_cases = [TEST_ASYNC_COMP_LIST, TEST_ASYNC_COMP_DICT, TEST_ASYNC_COMP_SET, TEST_ASYNC_COMP_FILTER, TEST_ASYNC_COMP_NESTED, TEST_ASYNC_COMP_GENERATOR, TEST_ASYNC_COMP_MIXED]
results = run_test_suite(test_cases)
for detail in results['details']:
    print('\n' + detail['report'])
else:
    print_test_summary(results)
