import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryWhileCond(ExhaustiveTestCase):
    """Bug R3-09: ternary 在 while 条件中 — 字节码不一致。

    原始:
        while (a if cond else b):
            pass
    缺陷: ternary 作为 while 条件时，每次循环都需重新求值 ternary，
         GET_ITER 与 POP_JUMP_IF_FALSE 的交互复杂。
         反编译器可能丢失 while 结构或 ternary 结构。
    """
    SOURCE_CODE = """while (a if cond else b):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
