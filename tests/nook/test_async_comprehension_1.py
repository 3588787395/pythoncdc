"""
测试状态: ❌ 失败
优先级: P1
相关任务: 任务2.3

描述:
    测试异步推导式

当前问题:
    - 完全不支持异步推导式
    - 无法识别 [x async for x in iter] 模式

期望输出:
    应正确生成异步推导式语法
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 异步列表推导式
TEST_ASYNC_COMP_LIST = DecompileTestCase(
    name="async_comp_list",
    source_code='''
async def get_results():
    return [x async for x in async_iter()]
'''.strip(),
    expected_patterns=["async def", "async for", "async_iter"]
)

# 测试用例2: 异步字典推导式
TEST_ASYNC_COMP_DICT = DecompileTestCase(
    name="async_comp_dict",
    source_code='''
async def get_mapping():
    return {k: v async for k, v in async_items()}
'''.strip(),
    expected_patterns=["async def", "async for", "async_items"]
)

# 测试用例3: 异步集合推导式
TEST_ASYNC_COMP_SET = DecompileTestCase(
    name="async_comp_set",
    source_code='''
async def get_unique():
    return {x async for x in async_iter()}
'''.strip(),
    expected_patterns=["async def", "async for"]
)

# 测试用例4: 带条件的异步推导式
TEST_ASYNC_COMP_FILTER = DecompileTestCase(
    name="async_comp_filter",
    source_code='''
async def get_filtered():
    return [x async for x in async_iter() if x > 0]
'''.strip(),
    expected_patterns=["async for", "if x > 0"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("ASYNC COMPREHENSION 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_ASYNC_COMP_LIST.source_code, "async_comp_list")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_ASYNC_COMP_LIST, TEST_ASYNC_COMP_DICT, TEST_ASYNC_COMP_SET, TEST_ASYNC_COMP_FILTER]:
        success = test.run()
        print(test.get_report())
        print()
