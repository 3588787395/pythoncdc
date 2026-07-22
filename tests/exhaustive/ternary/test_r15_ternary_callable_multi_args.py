import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryCallableMultiArgs(ExhaustiveTestCase):
    """Bug R15 (new): (a if c else b)(x, y) — ternary as callable with multi args。

    原始:
        (a if c else b)(x, y)
    缺陷: ternary 作为可调用对象，后接多参数 (x, y)。cond_block preload
         无 PUSH_NULL（ternary 自身作为 callable），ternary merge 块栈顶作为
         CALL 的 callable，由 LOAD x + LOAD y + PRECALL + CALL 2 消费。
         验证 ternary as callable + 多参数变体。
    """
    SOURCE_CODE = """(a if c else b)(x, y)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
