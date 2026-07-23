import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryChainedCompareBothTernary(ExhaustiveTestCase):
    """Bug R19-10: (t1) < (t2) < g — 链式比较两端均为 ternary。

    原始:
        x = (a if c else b) < (d if e else f) < g
    缺陷: 链式比较 a < b < c 的左操作数与中操作数都是 ternary。R3/R4/R5
         chained_compare 系列测过单 ternary 在左/右/中位置，R16 chained_compare_middle
         测过 `a < (ternary) < b` (单 ternary 中间)。本用例两个 ternary 分别在
         左与中：SWAP+COPY+COMPARE_OP+JUMP_IF_FALSE_OR_POP 链式比较模板中，两个
         ternary merge 块先后汇聚，反编译退化为两段独立表达式 `(t1)` 与
         `if (t2): pass`，完全丢失链式比较与赋值结构。
    """
    SOURCE_CODE = """x = (a if c else b) < (d if e else f) < g
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
