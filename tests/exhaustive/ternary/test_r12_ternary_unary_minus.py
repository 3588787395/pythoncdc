import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryUnaryMinus(ExhaustiveTestCase):
    """Bug R12 (new): -(a if c else b) — UNARY_NEGATIVE 消费 ternary。

    原始:
        x = -(a if c else b)
    缺陷: ternary 作为一元负号的操作数。merge_block 中 UNARY_NEGATIVE
         消费 ternary 结果。R2 已测 not (ternary) (test_r2_ternary_in_unary_not)，
         R12 测 unary minus 变体：UNARY_NEGATIVE 与 UNARY_NOT 不同，
         且 not 是 BoolOp 短路重写，- 是纯算术。
    """
    SOURCE_CODE = """x = -(a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
