import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernaryAsyncForSubscr(ExhaustiveTestCase):
    """Bug R18-05: async for x in y[(a if c else b)]: pass — async for iter 是 subscript 含 ternary。

    原始:
        async def f():
            async for x in y[(a if c else b)]:
                pass
    缺陷: async for 的 iter 表达式是 y[(ternary)] —— subscript 下标是 ternary。
         R8 async_for_iter 测过 `async for x in (ternary)` (ternary 直接作 iter)，
         R7 async_for 测过 body 内 ternary。本用例 ternary 是 subscript 的下标，
         ternary merge 块的 BINARY_SUBSCR 后才走 GET_AITER + GET_ANEXT + YIELD_VALUE
         轮询。反编译丢失 subscript 与 ternary，退化为 `async for x in y:`，
         字节码指令数不匹配 (18 vs 16)。
    """
    SOURCE_CODE = """async def f():
    async for x in y[(a if c else b)]:
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
