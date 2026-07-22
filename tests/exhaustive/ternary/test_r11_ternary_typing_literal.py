import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryTypingLiteral(ExhaustiveTestCase):
    """Bug R11 (new): typing.Literal + ternary annotation value.

    原始:
        from typing import Literal
        x: Literal['a', 'b'] = ('a' if c else 'b')
    缺陷: AnnAssign 的 annotation 是 Subscript(Name('Literal'), Tuple(...))，
         value 是 ternary。SETUP_ANNOTATIONS + LOAD_NAME Literal + LOAD_CONST
         'a' + LOAD_CONST 'b' + BUILD_TUPLE 2 + BUILD_CONST_KEY_MAP +
         STORE_ANNOTATIONS 'x' + ternary merge + STORE_NAME x。可能暴露
         annotation 重建与 ternary 归属的冲突。
    """
    SOURCE_CODE = """from typing import Literal
x: Literal['a', 'b'] = ('a' if c else 'b')
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
