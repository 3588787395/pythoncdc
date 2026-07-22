import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryYieldWithBinop(ExhaustiveTestCase):
    """Bug R14 (new): yield (a if c else b) + 1 — yield 表达式值含 ternary 与 binop。

    原始:
        def gen():
            yield (a if c else b) + 1
    缺陷: ternary 作为 yield 表达式的 BINARY_OP 输入。ternary merge 块栈输出
         被 BINARY_ADD 消费，再由 YIELD_VALUE 弹出。R2/R3/R4 已测过 yield ternary
         单值场景。R14 测 yield (ternary + const) 变体：ternary merge 之后还有
         BINARY_OP + YIELD_VALUE 消费链。
    """
    SOURCE_CODE = """def gen():
    yield (a if c else b) + 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
