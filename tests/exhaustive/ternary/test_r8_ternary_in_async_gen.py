import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInAsyncGen(ExhaustiveTestCase):
    """Bug R8: async generator + return ternary (隐式 None) — 字节码不一致。

    原始:
        async def g():
            yield a if c else b
    缺陷: async generator 中 yield ternary。R6 已测过 async_gen。
         R8 测 yield ternary 变体：ternary merge 块作为 YIELD_VALUE
         的源，与 async gen 的 GET_AWAITABLE + SEND polling 路径
         可能冲突。
    """
    SOURCE_CODE = """async def g():
    yield a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
