import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernarySlotsClass(ExhaustiveTestCase):
    """Bug R9: __slots__ 类 + ternary 属性 — 字节码不一致。

    原始:
        class C:
            __slots__ = ('x', 'y')
            attr = a if c else b
    缺陷: __slots__ 类中 ternary 属性赋值。__slots__ 元组 BUILD_TUPLE 2
         + STORE_NAME __slots__ 与后续 ternary merge 块的 STORE_NAME attr
         在同一 class code object，可能暴露 __slots__ 元组构建与 ternary
         归属的冲突。
    """
    SOURCE_CODE = """class C:
    __slots__ = ('x', 'y')
    attr = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
