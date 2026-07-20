import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryWhileCond(ExhaustiveTestCase):
    """Bug R4-06: ternary 作为 while 条件（带循环体）— 字节码不一致。

    原始:
        while (a if cond else b):
            x = 1
    缺陷: ternary 作为 while 条件时，每次循环都需重新求值 ternary，
         GET_ITER 与 POP_JUMP_IF_FALSE 的交互复杂，且循环体含赋值语句。
         反编译器可能丢失 while 结构或 ternary 结构。
         R3 已识别为已知限制（R3-09），R4 用非空循环体加重复杂度。
    """
    SOURCE_CODE = """while (a if cond else b):
    x = 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
