# Source Generated with Decompyle++ (Python version)
# File: test_async_for_1.cpython-311.pyc (Python 3.11)

__doc__ = '\n测试状态: ⚠️ 部分\n优先级: P1\n相关任务: 任务2.1\n\n描述:\n    测试 async for 循环的正确识别和反编译\n\n当前问题:\n    - 复杂场景下 async for 可能丢失 async 关键字\n    - GET_AITER/GET_ANEXT/END_ASYNC_FOR 指令处理不完善\n\n期望输出:\n    应正确包含 async for 关键字\n'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from tests.other.test_utils import DecompileTestCase, disassemble_code
TEST_ASYNC_FOR_BASIC = DecompileTestCase(name='async_for_basic', source_code='\nasync def process_items():\n    async for item in async_generator():\n        print(item)\n'.strip(), expected_patterns=['async def', 'async for', 'in async_generator()'])
TEST_ASYNC_FOR_ELSE = DecompileTestCase(name='async_for_else', source_code='\nasync def search():\n    async for item in items:\n        if item.found:\n            return item\n    else:\n        return None\n'.strip(), expected_patterns=['async for', 'else:', 'return None'])
TEST_ASYNC_FOR_NESTED = DecompileTestCase(name='async_for_nested', source_code='\nasync def nested():\n    async for outer in outer_iter():\n        async for inner in inner_iter(outer):\n            process(inner)\n'.strip(), expected_patterns=['async for outer', 'async for inner', 'process'])
if __name__ == '__main__':
    pass
for test in (TEST_ASYNC_FOR_BASIC, TEST_ASYNC_FOR_ELSE, TEST_ASYNC_FOR_NESTED):
    success = test.run()
    print(test.get_report())
    print()
