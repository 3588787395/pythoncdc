import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInAsyncFor(ExhaustiveTestCase):
    """Bug R7: async for body 中 ternary 赋值 — 字节码不一致。

    原始:
        async def f():
            async for x in ys:
                y = a if c else b
    缺陷: async for 语句 body 中包含 ternary 赋值。async for 的
         GET_AITER + GET_ANEXT + GET_AWAITABLE + SEND 轮询路径
         与 ternary merge 块的归属关系比同步 for 更复杂。
         期望 ternary 正确归约；当前疑似 async for 的 await polling
         与 ternary entry/merge 块共享导致归属冲突。
    """
    SOURCE_CODE = """async def f():
    async for x in ys:
        y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
