import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryNonlocalNestedFunc(ExhaustiveTestCase):
    """Bug R14 (new): nonlocal x; x = (a if c else b) — nonlocal 嵌套函数 ternary 赋值。

    原始:
        def outer():
            x = 0
            def inner():
                nonlocal x
                x = (a if c else b)
    缺陷: 嵌套函数中 nonlocal 声明后 ternary 赋值。R7/R8 已测 nonlocal ternary。
         R14 测 outer + inner + nonlocal + ternary 完整变体：inner 函数的
         LOAD_DEREF x + ternary merge + STORE_DEREF x 与 outer 的 LOAD_CONST 0 +
         STORE_DEREF x 可能在嵌套 code object 边界出现归属冲突。
    """
    SOURCE_CODE = """def outer():
    x = 0
    def inner():
        nonlocal x
        x = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
