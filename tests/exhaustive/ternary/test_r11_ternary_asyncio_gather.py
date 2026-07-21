import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryAsyncioGather(ExhaustiveTestCase):
    """Bug R11 (new): asyncio.gather + ternary arg.

    原始:
        import asyncio
        async def main():
            return await asyncio.gather((f() if c else g()), h())
    缺陷: ternary 作为 asyncio.gather 的第一个位置参数，整个 gather(ternary,
         h()) 被 await。ternary merge 块的栈输出作为 gather Call 的第一个 arg；
         cond_block 内含 PUSH_NULL + LOAD_NAME f + PRECALL 0 + CALL 0 (或 g)
         preload。await + ternary + Call 三重路径共存。
    """
    SOURCE_CODE = """import asyncio
async def main():
    return await asyncio.gather((f() if c else g()), h())
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
