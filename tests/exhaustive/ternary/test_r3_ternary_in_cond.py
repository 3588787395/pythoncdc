import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryInCond(ExhaustiveTestCase):
    """Bug R3-19: ternary 在另一个 ternary 的条件中 — 字节码不一致。

    原始: x = a if (b if c else d) else e
    缺陷: 嵌套 ternary 在外层 ternary 的条件部分时，POP_JUMP_IF_FALSE 链
         可能导致内层 ternary 被误识别为 BoolOp。反编译器可能丢失外层 ternary。
    """
    SOURCE_CODE = """x = a if (b if c else d) else e"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
