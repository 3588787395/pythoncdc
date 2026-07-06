"""
测试状态: ⚠️ 部分
优先级: P1
相关任务: 任务2.1

描述:
    测试 async for 循环的正确识别和反编译

当前问题:
    - 复杂场景下 async for 可能丢失 async 关键字
    - GET_AITER/GET_ANEXT/END_ASYNC_FOR 指令处理不完善

期望输出:
    应正确包含 async for 关键字
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 基本 async for
TEST_ASYNC_FOR_BASIC = DecompileTestCase(
    name="async_for_basic",
    source_code='''
async def process_items():
    async for item in async_generator():
        print(item)
'''.strip(),
    expected_patterns=["async def", "async for", "in async_generator()"]
)

# 测试用例2: async for with else
TEST_ASYNC_FOR_ELSE = DecompileTestCase(
    name="async_for_else",
    source_code='''
async def search():
    async for item in items:
        if item.found:
            return item
    else:
        return None
'''.strip(),
    expected_patterns=["async for", "else:", "return None"]
)

# 测试用例3: 嵌套 async for
TEST_ASYNC_FOR_NESTED = DecompileTestCase(
    name="async_for_nested",
    source_code='''
async def nested():
    async for outer in outer_iter():
        async for inner in inner_iter(outer):
            process(inner)
'''.strip(),
    expected_patterns=["async for outer", "async for inner", "process"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("ASYNC FOR 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_ASYNC_FOR_BASIC.source_code, "async_for_basic")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_ASYNC_FOR_BASIC, TEST_ASYNC_FOR_ELSE, TEST_ASYNC_FOR_NESTED]:
        success = test.run()
        print(test.get_report())
        print()
