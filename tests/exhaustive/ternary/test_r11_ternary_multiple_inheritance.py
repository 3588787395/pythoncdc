import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryMultipleInheritance(ExhaustiveTestCase):
    """Bug R11 (new): multiple inheritance + ternary in method body.

    原始:
        class A:
            def m(self):
                return (a if c else b)
        class B:
            def m(self):
                return (x if c2 else y)
        class C(A, B):
            def m(self):
                return (p if c3 else q)
    缺陷: 三个类通过多继承形成菱形（A, B, C(A,B)），每个类的 m() 都含 ternary。
         C 的 __build_class__ Call 的 args 包含两个 base (A, B)，且类体
         m() 内 ternary merge 块的 RETURN_VALUE 与多继承 base 加载栈
         LOAD_NAME A + LOAD_NAME B 共存。依「自底向上归约」：每个 ternary 在
         其 code object 内独立归约；多继承只影响 __build_class__ 的 args 数。
    """
    SOURCE_CODE = """class A:
    def m(self):
        return (a if c else b)
class B:
    def m(self):
        return (x if c2 else y)
class C(A, B):
    def m(self):
        return (p if c3 else q)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
