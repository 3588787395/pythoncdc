import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryAsyncForNestedBody(ExhaustiveTestCase):
    """Bug R9: async for body 多层嵌套 ternary — 字节码不一致。

    原始:
        async def f():
            async for x in ys:
                z = (a if c1 else (b if c2 else d))
    缺陷: R7-02 已知 async for body 内简单 ternary 失败。R9 测多层
         嵌套 ternary 变体：内层 ternary 的 merge 块作为外层 ternary
         的 false_value 块，两层 ternary 的 entry/merge 与 async for
         的 GET_AITER + GET_ANEXT + SEND polling 路径共享同一 code
         object，可能暴露三层归属冲突。
    """
    SOURCE_CODE = """async def f():
    async for x in ys:
        z = (a if c1 else (b if c2 else d))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
