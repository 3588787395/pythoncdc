import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernaryDictcompIter(ExhaustiveTestCase):
    """Bug R16 (new): {k: v for k, v in (a if c else b)} — dictcomp iter is ternary。

    原始:
        x = {k: v for k, v in (a if c else b)}
    缺陷: dict comprehension 的 iter 表达式是 ternary。dictcomp 中 ternary
         merge 块作为 GET_ITER 源，UNPACK_SEQUENCE 2 + STORE k/v 与
         ternary region 边界冲突。
    """
    SOURCE_CODE = """x = {k: v for k, v in (a if c else b)}
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
