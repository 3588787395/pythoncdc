import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInAwait(ExhaustiveTestCase):
    """Bug R2-30: ternary 在 await 表达式中 — 字节码不一致。

    原始:
        async def f():
            return await (a if cond else b)
    缺陷: ternary 在 await 中时，GET_AWAITABLE + SEND 循环消费 ternary 结果。
         反编译器可能丢失 await 结构。
    """
    SOURCE_CODE = """async def f():
    return await (a if cond else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
