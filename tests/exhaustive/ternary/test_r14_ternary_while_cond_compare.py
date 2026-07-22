import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryWhileCondCompare(ExhaustiveTestCase):
    """Bug R14 (new): while (a if c else b) > 0: pass — while 条件是 ternary 与常量比较。

    原始:
        while (a if c else b) > 0:
            pass
    缺陷: while 条件是 ternary 与常量比较。R3 ternary_while_cond 测过 while (ternary):
         直接作为条件。R14 测 while (ternary) > 0 变体：ternary merge 之后 COMPARE_OP
         + POP_JUMP_IF_FALSE 跳回 while 顶。COMPARE_OP 消费 ternary 与 LOAD_CONST 0，
         while polling 循环 + ternary merge + COMPARE_OP 共存场景。
    """
    SOURCE_CODE = """while (a if c else b) > 0:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
