import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryDynamicClassType(ExhaustiveTestCase):
    """Bug R11 (new): dynamic class creation type() + ternary default attr.

    原始:
        C = type('C', (), {'x': (a if c else b)})
    缺陷: type(name, bases, dict) 三参形式动态创建类，dict 字面量内 value 是
         ternary。BUILD_MAP + LOAD_CONST 'x' + ternary merge + STORE_MAP +
         PUSH_NULL + LOAD_NAME type + LOAD_CONST 'C' + BUILD_TUPLE 0 +
         LOAD_CONST <map> + PRECALL 3 + CALL 3 + STORE_NAME C。ternary merge
         块在 dict 字面量构造时被消费，可能暴露 ternary consumer 在 dict
         value 槽位的归属冲突。
    """
    SOURCE_CODE = """C = type('C', (), {'x': (a if c else b)})
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
