import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryPropertySetter(ExhaustiveTestCase):
    """Bug R9: property + setter + ternary — 字节码不一致。

    原始:
        class C:
            @property
            def x(self):
                return self._x if c else 0
            @x.setter
            def x(self, v):
                self._x = v if c2 else 0
    缺陷: property getter 和 setter 都含 ternary。R7 已测过 property。
         R9 测 property + setter + 双 ternary 变体：两个 ternary 在
         不同的 code object 内，但共享同一 class body，可能暴露
         property 装饰器栈与 ternary merge 块的归属冲突。
    """
    SOURCE_CODE = """class C:
    @property
    def x(self):
        return self._x if c else 0
    @x.setter
    def x(self, v):
        self._x = v if c2 else 0
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
