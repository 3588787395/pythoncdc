"""
测试状态: ⚠️ 部分
优先级: P1
相关任务: 任务2.2

描述:
    测试嵌套 async with 的正确标记

当前问题:
    - 多层嵌套 async with 可能丢失 async 标记

期望输出:
    所有 with 语句都应正确标记为 async with
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 基本 async with
TEST_ASYNC_WITH_BASIC = DecompileTestCase(
    name="async_with_basic",
    source_code='''
async def use_context():
    async with get_context() as ctx:
        await ctx.process()
'''.strip(),
    expected_patterns=["async def", "async with", "await"]
)

# 测试用例2: 嵌套 async with
TEST_ASYNC_WITH_NESTED = DecompileTestCase(
    name="async_with_nested",
    source_code='''
async def nested_contexts():
    async with outer_ctx() as outer:
        async with inner_ctx() as inner:
            result = await outer.combine(inner)
            return result
'''.strip(),
    expected_patterns=["async with outer_ctx", "async with inner_ctx", "await"]
)

# 测试用例3: 多上下文 async with
TEST_ASYNC_WITH_MULTIPLE = DecompileTestCase(
    name="async_with_multiple",
    source_code='''
async def multiple_contexts():
    async with ctx1() as a, ctx2() as b, ctx3() as c:
        return await process(a, b, c)
'''.strip(),
    expected_patterns=["async with", "ctx1()", "ctx2()", "ctx3()", "await"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("ASYNC WITH 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_ASYNC_WITH_NESTED.source_code, "async_with_nested")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_ASYNC_WITH_BASIC, TEST_ASYNC_WITH_NESTED, TEST_ASYNC_WITH_MULTIPLE]:
        success = test.run()
        print(test.get_report())
        print()
