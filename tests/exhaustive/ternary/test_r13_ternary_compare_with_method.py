import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryCompareWithMethod(ExhaustiveTestCase):
    """Bug R13 (new): x.method() == (a if c else b) — compare + method + ternary。

    原始:
        x.method() == (a if c else b)
    缺陷: ternary 在比较表达式 (==) 的右操作数。左操作数是 method call
         x.method()，右操作数是 ternary。字节码：LOAD x + LOAD_ATTR method +
         PRECALL + CALL 0 + ternary merge + COMPARE_OP ==。R2 已测 ternary_in
         _compare_right（test_r2_ternary_in_compare_right，左操作数是变量
         x），R13 测左操作数是 method call 的变体（验证 method chain 在 compare
         左侧时不影响 ternary 归约）。
    """
    SOURCE_CODE = """x.method() == (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
