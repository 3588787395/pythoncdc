import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInNonlocalThenAssign(ExhaustiveTestCase):
    """Bug R8: nonlocal 声明后紧跟 ternary 赋值 — 字节码不一致。

    原始:
        def outer():
            x = 1
            def inner():
                nonlocal x
                x = a if c else b
    缺陷: 嵌套函数内 nonlocal 声明后紧跟 ternary 赋值。R7 已测过
         nonlocal_complex。R8 测 nonlocal + ternary 直接赋值变体：
         nonlocal x 的 STORE_DEREF 与 ternary merge 块的 STORE_DEREF x
         可能共享 entry 块导致归属冲突。
    """
    SOURCE_CODE = """def outer():
    x = 1
    def inner():
        nonlocal x
        x = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
