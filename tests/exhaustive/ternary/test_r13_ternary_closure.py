import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryClosure(ExhaustiveTestCase):
    """Bug R13 (new): def f(): x = (a if c else b); return lambda: x — closure ternary。

    原始:
        def f():
            x = (a if c else b)
            return lambda: x
    缺陷: ternary 在外层函数体内（赋值给 x），内层 lambda 闭包捕获 x。
         ternary merge 块 STORE_NAME x 在外层函数 code object 中，内层
         lambda 通过 LOAD_DEREF x 引用闭包变量。R6 已测 ternary_closure
         _capture，R13 重测确认 R12 修复无退化。
    """
    SOURCE_CODE = """def f():
    x = (a if c else b)
    return lambda: x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
