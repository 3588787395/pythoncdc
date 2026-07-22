import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryAsyncGenYieldTernary(ExhaustiveTestCase):
    """Bug R9: async generator yield ternary + 后续语句 — 字节码不一致。

    原始:
        async def g():
            yield a if c else b
            x = 1
    缺陷: R6/R8 已测 async gen yield ternary。R9 测 yield ternary 后
         跟普通赋值变体：ternary merge 块作为 YIELD_VALUE 源，yield 后
         的 STORE_NAME x 与 async gen 的 RESUME + GET_AWAITABLE + SEND
         polling 路径在 merge 块之后，可能暴露 yield 退出与后续块的归属
         冲突。
    """
    SOURCE_CODE = """async def g():
    yield a if c else b
    x = 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
