import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryCompareInBothTernary(ExhaustiveTestCase):
    """Bug R19-11: (t1) in (t2) — `in` 比较两端均为 ternary。

    原始:
        x = (a if c else b) in (d if e else f)
    缺陷: 二元比较 `in` 的左右操作数都是 ternary。R5 compare_in 测过
         `(ternary) in seq` (左 ternary，右常量)，R2 contains 测过
         `x in (ternary)` (左常量，右 ternary)。本用例两端均 ternary：
         COMPARE_OP (in) 消费栈顶两个 ternary 结果，两个 ternary merge 块
         先后汇聚，反编译退化为两段独立表达式 `(t1)` 与 `x = (t2)`，丢失
         `in` 比较与第一 ternary。
    """
    SOURCE_CODE = """x = (a if c else b) in (d if e else f)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
