import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryAttrOnTernary(ExhaustiveTestCase):
    """Bug R15 (new): (a if c else b).attr — attribute access on ternary。

    原始:
        (a if c else b).attr
    缺陷: ternary 作为 attribute access 的对象。ternary merge 块栈顶作为
         LOAD_ATTR 的 obj。R2 已测 ternary_in_attribute (有赋值)，R15 测
         无赋值 Expr 语句 + 简单 attr access 变体。
    """
    SOURCE_CODE = """(a if c else b).attr
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
