import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInClassBodyAssign(ExhaustiveTestCase):
    """Bug R8: 类体中 ternary 赋值（带 method def 后） — 字节码不一致。

    原始:
        class C:
            attr = a if c else b
            def m(self):
                return self.attr
    缺陷: 类体中先 ternary 赋值，后跟方法定义。R5 已测过 class body
         ternary。R8 测带方法定义变体：ternary merge 块的 STORE_NAME attr
         与后续 MAKE_FUNCTION + STORE_NAME m 在同一 code object，
         可能暴露 class body 块结构与 ternary 归属的冲突。
    """
    SOURCE_CODE = """class C:
    attr = a if c else b
    def m(self):
        return self.attr
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
