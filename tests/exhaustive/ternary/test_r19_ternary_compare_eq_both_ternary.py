import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryCompareEqBothTernary(ExhaustiveTestCase):
    """Bug R19-13: (t1) == (t2) — `==` 比较两端均为 ternary。

    原始:
        x = (a if c else b) == (d if e else f)
    缺陷: 二元比较 `==` 的左右操作数都是 ternary。R1 ternary_in_compare 测过
         `(ternary) == x` (左 ternary，右常量)，R2 compare_right 测过
         `x == (ternary)` (左常量，右 ternary)。本用例两端均 ternary：
         COMPARE_OP (==) 消费栈顶两个 ternary 结果，两个 ternary merge 块
         先后汇聚，反编译退化为两段独立表达式 `(t1)` 与 `x = (t2)`，丢失
         `==` 比较与第一 ternary。
    """
    SOURCE_CODE = """x = (a if c else b) == (d if e else f)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
