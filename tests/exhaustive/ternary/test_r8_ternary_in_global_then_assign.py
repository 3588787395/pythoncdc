import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInGlobalThenAssign(ExhaustiveTestCase):
    """Bug R8: global 声明后紧跟 ternary 赋值 — 字节码不一致。

    原始:
        def f():
            global x
            x = a if c else b
    缺陷: 函数内 global 声明后紧跟 ternary 赋值。R7 已测过 global_complex。
         R8 测 global + ternary 直接赋值变体：global x 的 STORE_GLOBAL
         与 ternary merge 块的 STORE_GLOBAL x 可能共享 entry 块导致
         归属冲突。
    """
    SOURCE_CODE = """def f():
    global x
    x = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
