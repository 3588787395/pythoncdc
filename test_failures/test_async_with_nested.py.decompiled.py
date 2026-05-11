# Source Generated with Decompyle++ (Python version)
# File: test_async_with_nested.cpython-311.pyc (Python 3.11)

__doc__ = '\n测试状态: ⚠️ 部分\n优先级: P1\n相关任务: 任务2.2\n\n描述:\n    测试嵌套 async with 的正确标记\n\n当前问题:\n    - 多层嵌套 async with 可能丢失 async 标记\n\n期望输出:\n    所有 with 语句都应正确标记为 async with\n'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from tests.other.test_utils import DecompileTestCase, disassemble_code
TEST_ASYNC_WITH_BASIC = DecompileTestCase(name='async_with_basic', source_code='\nasync def use_context():\n    async with get_context() as ctx:\n        await ctx.process()\n'.strip(), expected_patterns=['async def', 'async with', 'await'])
TEST_ASYNC_WITH_NESTED = DecompileTestCase(name='async_with_nested', source_code='\nasync def nested_contexts():\n    async with outer_ctx() as outer:\n        async with inner_ctx() as inner:\n            result = await outer.combine(inner)\n            return result\n'.strip(), expected_patterns=['async with outer_ctx', 'async with inner_ctx', 'await'])
TEST_ASYNC_WITH_MULTIPLE = DecompileTestCase(name='async_with_multiple', source_code='\nasync def multiple_contexts():\n    async with ctx1() as a, ctx2() as b, ctx3() as c:\n        return await process(a, b, c)\n'.strip(), expected_patterns=['async with', 'ctx1()', 'ctx2()', 'ctx3()', 'await'])
if __name__ == '__main__':
    pass
for test in (TEST_ASYNC_WITH_BASIC, TEST_ASYNC_WITH_NESTED, TEST_ASYNC_WITH_MULTIPLE):
    success = test.run()
    print(test.get_report())
    print()
