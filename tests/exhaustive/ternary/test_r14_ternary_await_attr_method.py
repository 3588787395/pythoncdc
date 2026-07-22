import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryAwaitAttrMethod(ExhaustiveTestCase):
    """Bug R14 (new): await (a if c else b).method() — await ternary with attr method。

    原始:
        async def f():
            x = await (a if c else b).method()
    缺陷: ternary 作为 await 表达式，且 ternary 之后再链式 LOAD_METHOD method +
         PRECALL + CALL。R2/R3/R4 已测 await ternary 单值场景，R5 测过 await_complex。
         R14 测 await ternary + method 链变体：ternary merge 之后还有 LOAD_METHOD +
         PRECALL + CALL 消费链，再由 GET_AWAITABLE + SEND polling 循环消费。
    """
    SOURCE_CODE = """async def f():
    x = await (a if c else b).method()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
