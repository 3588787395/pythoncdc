# Source Generated with Decompyle++ (Python version)
# File: test_async_comprehension_1.cpython-311.pyc (Python 3.11)

__doc__ = '\n测试状态: ❌ 失败\n优先级: P1\n相关任务: 任务2.3\n\n描述:\n    测试异步推导式\n\n当前问题:\n    - 完全不支持异步推导式\n    - 无法识别 [x async for x in iter] 模式\n\n期望输出:\n    应正确生成异步推导式语法\n'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from tests.other.test_utils import DecompileTestCase, disassemble_code
TEST_ASYNC_COMP_LIST = DecompileTestCase(name='async_comp_list', source_code='\nasync def get_results():\n    return [x async for x in async_iter()]\n'.strip(), expected_patterns=['async def', 'async for', 'async_iter'])
TEST_ASYNC_COMP_DICT = DecompileTestCase(name='async_comp_dict', source_code='\nasync def get_mapping():\n    return {k: v async for k, v in async_items()}\n'.strip(), expected_patterns=['async def', 'async for', 'async_items'])
TEST_ASYNC_COMP_SET = DecompileTestCase(name='async_comp_set', source_code='\nasync def get_unique():\n    return {x async for x in async_iter()}\n'.strip(), expected_patterns=['async def', 'async for'])
TEST_ASYNC_COMP_FILTER = DecompileTestCase(name='async_comp_filter', source_code='\nasync def get_filtered():\n    return [x async for x in async_iter() if x > 0]\n'.strip(), expected_patterns=['async for', 'if x > 0'])
if __name__ == '__main__':
    pass
for test in (TEST_ASYNC_COMP_LIST, TEST_ASYNC_COMP_DICT, TEST_ASYNC_COMP_SET, TEST_ASYNC_COMP_FILTER):
    success = test.run()
    print(test.get_report())
    print()
