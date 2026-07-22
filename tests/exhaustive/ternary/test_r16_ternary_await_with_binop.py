import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernaryAwaitWithBinop(ExhaustiveTestCase):
    """Bug R16 (new): await (a if c else b) + 1 — await + binop chain。

    原始:
        async def f():
            return await (a if c else b) + 1
    缺陷: ternary 作为 await 表达式 + 1 binary op。
         ternary merge 块栈顶经 GET_AWAITABLE + SEND polling
         + BINARY_OP + RETURN_VALUE 消费链。R3 await_expr 已测过
         await ternary 单值，R16 测 await ternary + binop 变体。
    """
    SOURCE_CODE = """async def f():
    return await (a if c else b) + 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
