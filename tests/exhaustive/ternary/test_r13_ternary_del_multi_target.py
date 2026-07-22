import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryDelMultiTarget(ExhaustiveTestCase):
    """Bug R13 (new): del obj.attr, lst[a if c else b] — del multiple targets with ternary subscript。

    原始:
        del obj.attr, lst[a if c else b]
    缺陷: del 语句多目标，其中一个是 ternary subscript (lst[ternary])。
         字节码：LOAD obj + DELETE_ATTR attr + LOAD lst + ternary merge +
         DELETE_SUBSCR。R4 已测 ternary_in_del_target 单纯场景，R7 已测
         ternary_in_del_obj_subscript。R13 测 del 多目标 + ternary subscript
         作为第二目标的复合场景。
    """
    SOURCE_CODE = """del obj.attr, lst[a if c else b]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
