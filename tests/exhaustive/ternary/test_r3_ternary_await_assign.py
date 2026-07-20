import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryAwaitAssign(ExhaustiveTestCase):
    """Bug R3-03: ternary 在 await 表达式中赋值 — 字节码不一致。

    原始:
        async def f():
            x = await (a if cond else b)
    缺陷: ternary 在 await 中赋值时，GET_AWAITABLE + SEND 循环消费 ternary 结果，
         随后 STORE_FAST 消费 await 结果。反编译器可能丢失 await 与赋值结构。
    """
    SOURCE_CODE = """async def f():
    x = await (a if cond else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
