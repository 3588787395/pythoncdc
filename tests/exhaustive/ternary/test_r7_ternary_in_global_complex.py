import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInGlobalComplex(ExhaustiveTestCase):
    """Bug R7: 模块顶层 global + ternary 重新赋值 — 字节码不一致。

    原始:
        x = 1
        def f():
            global x
            x = a if c else b
            return x
        f()
    缺陷: 模块顶层 x = 1 后，函数内 global x + ternary 重新赋值 + return。
         R3 已测简单 global + ternary (test_r3_ternary_global)，R5 测
         global + ternary + return (test_r5_ternary_in_global)。R7 在
         模块顶层增加 x = 1 初始赋值，使 STORE_GLOBAL 在嵌套 code object
         内的 LOAD_GLOBAL/STORE_GLOBAL 链与 ternary merge 块的归属关系
         更复杂。
    """
    SOURCE_CODE = """x = 1
def f():
    global x
    x = a if c else b
    return x
f()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
