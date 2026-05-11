"""
测试异步推导式的反编译

测试状态: 🔄 待验证
优先级: P1

描述:
    测试异步推导式（[x async for x in iter]）的正确反编译

期望输出:
    - 正确包含async for关键字在推导式中
    - 列表、字典、集合推导式都支持
    - 带条件的异步推导式正确处理
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary


# 测试用例1: 异步列表推导式
TEST_ASYNC_COMP_LIST = AsyncTestCase(
    name="async_comp_list",
    source_code='''
async def get_results():
    return [x async for x in async_iter()]
'''.strip(),
    expected_patterns=["async def", "async for", "async_iter"]
)

# 测试用例2: 异步字典推导式
TEST_ASYNC_COMP_DICT = AsyncTestCase(
    name="async_comp_dict",
    source_code='''
async def get_mapping():
    return {k: v async for k, v in async_items()}
'''.strip(),
    expected_patterns=["async def", "async for", "async_items"]
)

# 测试用例3: 异步集合推导式
TEST_ASYNC_COMP_SET = AsyncTestCase(
    name="async_comp_set",
    source_code='''
async def get_unique():
    return {x async for x in async_iter()}
'''.strip(),
    expected_patterns=["async def", "async for"]
)

# 测试用例4: 带条件的异步推导式
TEST_ASYNC_COMP_FILTER = AsyncTestCase(
    name="async_comp_filter",
    source_code='''
async def get_filtered():
    return [x async for x in async_iter() if x > 0]
'''.strip(),
    expected_patterns=["async for", "if x > 0"]
)

# 测试用例5: 嵌套异步推导式
TEST_ASYNC_COMP_NESTED = AsyncTestCase(
    name="async_comp_nested",
    source_code='''
async def get_nested():
    return [y async for x in outer_iter() async for y in inner_iter(x)]
'''.strip(),
    expected_patterns=["async for x", "async for y"]
)

# 测试用例6: 异步生成器表达式
TEST_ASYNC_COMP_GENERATOR = AsyncTestCase(
    name="async_comp_generator",
    source_code='''
async def get_gen():
    return (x * 2 async for x in async_iter())
'''.strip(),
    expected_patterns=["async def", "async for"]
)

# 测试用例7: 混合推导式
TEST_ASYNC_COMP_MIXED = AsyncTestCase(
    name="async_comp_mixed",
    source_code='''
async def process():
    # 列表推导式包含异步生成器
    items = [x async for x in async_gen()]
    # 普通列表推导式处理结果
    doubled = [x * 2 for x in items]
    return doubled
'''.strip(),
    expected_patterns=["async for", "for x in items"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("异步推导式测试")
    print("=" * 60)
    
    test_cases = [
        TEST_ASYNC_COMP_LIST,
        TEST_ASYNC_COMP_DICT,
        TEST_ASYNC_COMP_SET,
        TEST_ASYNC_COMP_FILTER,
        TEST_ASYNC_COMP_NESTED,
        TEST_ASYNC_COMP_GENERATOR,
        TEST_ASYNC_COMP_MIXED,
    ]
    
    results = run_test_suite(test_cases)
    
    for detail in results['details']:
        print("\n" + detail['report'])
    
    print_test_summary(results)
