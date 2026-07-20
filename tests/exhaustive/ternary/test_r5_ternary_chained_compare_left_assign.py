import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryChainedCompareLeftAssign(ExhaustiveTestCase):
    """Bug R5-04: ternary 在 chained compare 左端（2-term）+ 赋值 — 回归验证。

    原始: r = (a if c else b) < 10
    缺陷: R4-03 部分修复后此场景已通过（test_r4_ternary_chained_compare_left.py）。
         R5 重测以确认 R4 部分修复未退化，并作为对照（2-term vs 3/4/5-term）。
    """
    SOURCE_CODE = """r = (a if c else b) < 10"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
