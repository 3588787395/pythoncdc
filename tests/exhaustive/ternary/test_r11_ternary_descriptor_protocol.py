import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryDescriptorProtocol(ExhaustiveTestCase):
    """Bug R11 (new): descriptor protocol __get__/__set__ + ternary.

    原始:
        class Desc:
            def __get__(self, obj, owner=None):
                return (obj._x if c else None)
            def __set__(self, obj, value):
                obj._x = (value if c2 else 0)
    缺陷: descriptor protocol 的 __get__ return ternary + __set__ body ternary
         赋值。两个方法在不同 code object 内独立归约。__get__ 的 ternary merge
         块 RETURN_VALUE 是 Return(IfExp)；__set__ 的 ternary merge 块
         STORE_ATTR _x 是 Assign(Attribute, IfExp)。依「自底向上归约」：
         每个 ternary 在其 code object 内独立归约。
    """
    SOURCE_CODE = """class Desc:
    def __get__(self, obj, owner=None):
        return (obj._x if c else None)
    def __set__(self, obj, value):
        obj._x = (value if c2 else 0)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
