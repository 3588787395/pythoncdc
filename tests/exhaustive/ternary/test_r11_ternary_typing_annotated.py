import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryTypingAnnotated(ExhaustiveTestCase):
    """Bug R11 (new): typing.Annotated + ternary default.

    原始:
        from typing import Annotated
        x: Annotated[int, 'meta'] = (1 if c else 2)
    缺陷: AnnAssign annotation 是 Subscript(Name('Annotated'), Tuple(int, 'meta'))，
         value 是 ternary。Annotated 的多元素 Tuple 在 BINARY_SUBSCR 之前
         BUILD_TUPLE 2，与 ternary merge 块的 STORE_NAME x 共存。
    """
    SOURCE_CODE = """from typing import Annotated
x: Annotated[int, 'meta'] = (1 if c else 2)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
