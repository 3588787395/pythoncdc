import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernarySuperArg(ExhaustiveTestCase):
    """Bug R9: super() 参数是 ternary — 字节码不一致。

    原始:
        class C:
            def m(self):
                return super((C if c else D), self).m()
    缺陷: super() 第一个参数是 ternary。super() 的 LOAD_GLOBAL super +
         ternary merge + LOAD_NAME self + CALL 调用栈顺序，与后续
         LOAD_ATTR m + CALL 的链式调用可能冲突。
    """
    SOURCE_CODE = """class C:
    def m(self):
        return super((C if c else D), self).m()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
