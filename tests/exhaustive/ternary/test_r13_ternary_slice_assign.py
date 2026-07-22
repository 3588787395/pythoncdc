import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernarySliceAssign(ExhaustiveTestCase):
    """Bug R13 (new): x[0:1] = (a if c else b) — slice assignment ternary。

    原始:
        x[0:1] = (a if c else b)
    缺陷: ternary 作为 slice assignment 的右值。STORE_SUBSCR 前栈上有：
         LOAD_NAME x + LOAD_CONST 0 + LOAD_CONST 1 + BUILD_SLICE 2（slice 索引）
         + ternary merge 块栈输出 + STORE_SUBSCR。R2 已测 ternary_in_store_subscr
         （普通下标 x[0] = ternary），R12 已测 ternary_in_slice（slice load）。
         R13 测 slice store 模式（左值是 slice 表达式，右值是 ternary）。
    """
    SOURCE_CODE = """x[0:1] = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
