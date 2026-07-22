import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryAsyncForIterCall(ExhaustiveTestCase):
    """Bug R9: async for iter 含 ternary + call 表达式 — 字节码不一致。

    原始:
        async def f():
            async for x in g(a if c else b):
                pass
    缺陷: R8-08 已知 async for iter 简单 ternary 失败。R9 测 iter 表达式
         是 g(ternary) 变体：ternary merge 块作为 CALL 的参数，与
         async for 的 GET_AITER 源（CALL 结果）的栈顺序、async for 的
         polling 路径归属可能冲突。
    """
    SOURCE_CODE = """async def f():
    async for x in g(a if c else b):
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
