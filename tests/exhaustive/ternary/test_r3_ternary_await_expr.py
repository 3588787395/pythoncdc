import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryAwaitExpr(ExhaustiveTestCase):
    """Bug R3-04: ternary 在 await 表达式（无 return/assign）— 字节码不一致。

    原始:
        async def f():
            await (a if cond else b)
    缺陷: ternary 在 await 表达式中（无 return/assign 包装）时，
         GET_AWAITABLE + SEND 循环消费 ternary 结果，POP_TOP 丢弃 await 结果。
         反编译器可能丢失 await 结构。
    """
    SOURCE_CODE = """async def f():
    await (a if cond else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
