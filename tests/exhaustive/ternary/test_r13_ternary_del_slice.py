import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryDelSlice(ExhaustiveTestCase):
    """Bug R13 (new): del x[a if c else b : b if d else e] — del slice 双 ternary。

    原始:
        del x[a if c else b : b if d else e]
    缺陷: del slice 上下界均为 ternary。DELETE_SUBSCR 前栈上有：
         LOAD_NAME x + <ternary1> + <ternary2> + BUILD_SLICE 2 + DELETE_SUBSCR。
         R8 已测 ternary_del_subscript_both (del x[ternary1:ternary2])，R13 测
         del slice 双 ternary 场景，验证多 ternary 在 DELETE_SUBSCR 路径的归约。
    """
    SOURCE_CODE = """del x[a if c else b : b if d else e]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
