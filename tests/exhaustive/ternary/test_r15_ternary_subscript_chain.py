import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernarySubscriptChain(ExhaustiveTestCase):
    """Bug R15 (new): (a if c else b)[0][1] — chained subscript on ternary。

    原始:
        (a if c else b)[0][1]
    缺陷: ternary 后接 chained subscript [0][1]。ternary merge 块栈顶作为
         BINARY_SUBSCR 的 obj，CALL 0 后再 BINARY_SUBSCR。R4 ternary_in_subscript
         已测 x[ternary]（ternary 是 subscript index），R15 测 ternary 是
         subscript obj 的变体。
    """
    SOURCE_CODE = """(a if c else b)[0][1]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
