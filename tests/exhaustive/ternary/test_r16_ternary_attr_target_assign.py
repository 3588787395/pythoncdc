import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernaryAttrTargetAssign(ExhaustiveTestCase):
    """Bug R16 (new): (a if c else b).attr = x — ternary as attr assign obj。

    原始:
        (a if c else b).attr = x
    缺陷: ternary 作为 attribute assignment 的 base 对象（lhs）。
         cond_block preload 含 LOAD x，ternary merge 块栈顶作为
         STORE_ATTR attr 的 obj。R4 attr_assign 已测 x.attr = ternary
         （ternary 是 rhs），R16 测 ternary 是 lhs base 的变体。
    """
    SOURCE_CODE = """(a if c else b).attr = x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
