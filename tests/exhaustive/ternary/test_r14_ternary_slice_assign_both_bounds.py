import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernarySliceAssignBothBounds(ExhaustiveTestCase):
    """Bug R14 (new): x[(a if c else b):(d if e else f)] = 1 — slice assign 双 ternary 边界。

    原始:
        x[(a if c else b):(d if e else f)] = 1
    缺陷: subscript slice assign，slice 上下界都是 ternary。R13-02 修复了
         del_slice 双 ternary (del x[t:t])。R14 测 slice assign 双 ternary 变体：
         BUILD_SLICE 2 + STORE_SUBSCR 与 ternary merge 块归属可能冲突。
    """
    SOURCE_CODE = """x[(a if c else b):(d if e else f)] = 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
