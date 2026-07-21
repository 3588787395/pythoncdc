import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernaryChainedCompareMiddle(ExhaustiveTestCase):
    """Bug R16 (new): a < (b if c else d) < e — ternary in middle of chained compare。

    原始:
        a < (b if c else d) < e
    缺陷: ternary 作为 chained compare 中间项。R2 in_chained_compare 已测过
         ternary 在 chained compare，但 R2 测 `a < ternary < b` 形式，
         R16 重测确认无回归。
    """
    SOURCE_CODE = """a < (b if c else d) < e
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
