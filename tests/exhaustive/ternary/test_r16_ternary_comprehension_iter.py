import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernaryComprehensionIter(ExhaustiveTestCase):
    """Bug R16 (new): [v for v in (a if c else b)] — listcomp iter is ternary。

    原始:
        x = [v for v in (a if c else b)]
    缺陷: list comprehension 的 iter 表达式是 ternary。R8 for_iter 已测过
         普通 for iter ternary，R16 测 comprehension 内嵌套 code object
         中 ternary merge 块作为 GET_ITER 源。
    """
    SOURCE_CODE = """x = [v for v in (a if c else b)]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
