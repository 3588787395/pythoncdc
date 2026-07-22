import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryAttrDeleteSubscr(ExhaustiveTestCase):
    """Bug R13 (new): del obj[a if c else b] — del subscript with ternary index。

    原始:
        del obj[a if c else b]
    缺陷: ternary 作为 del subscript 的索引。DELETE_SUBSCR 前栈上有：
         LOAD_NAME obj + ternary merge 块栈输出 + DELETE_SUBSCR。R4 已测
         ternary_in_del_target (del x[ternary])，R7 已测 ternary_in_del_obj
         _subscript (del obj[ternary])，R13 重测验证 R12 修复无退化，作为
         baseline 对照。
    """
    SOURCE_CODE = """del obj[a if c else b]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
