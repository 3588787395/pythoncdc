import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryTypingUnion(ExhaustiveTestCase):
    """Bug R11 (new): typing.Union + ternary annotation value.

    原始:
        from typing import Union
        x: Union[int, str] = (1 if c else 's')
    缺陷: AnnAssign annotation 是 Subscript(Name('Union'), Tuple(...))，
         value 是 ternary。Union 的 LOAD_NAME + BUILD_TUPLE + BINARY_SUBSCR
         与 ternary merge 块的 STORE_NAME x 共存于 module code object。
    """
    SOURCE_CODE = """from typing import Union
x: Union[int, str] = (1 if c else 's')
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
