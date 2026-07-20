import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInUnaryNot(ExhaustiveTestCase):
    """Bug R2-4: ternary 与 UNARY_NOT 组合 — 字节码不一致。

    原始: x = not (a if cond else b)
    缺陷: UNARY_NOT 在 merge_block 中消费 ternary 结果。
         反编译器可能丢失 UNARY_NOT 与外层赋值。
    """
    SOURCE_CODE = """x = not (a if cond else b)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
