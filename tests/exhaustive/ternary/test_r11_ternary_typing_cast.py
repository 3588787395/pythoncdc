import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryTypingCast(ExhaustiveTestCase):
    """Bug R11 (new): typing.cast + ternary as casted value.

    原始:
        from typing import cast
        x = cast(int, (a if c else b))
    缺陷: typing.cast(int, ternary) 调用，ternary 作为第二个位置参数。
         PUSH_NULL + LOAD_NAME cast + LOAD_NAME int + ternary merge + PRECALL 2
         + CALL 2 + STORE_NAME x。ternary merge 块的栈输出作为 cast Call 的
         第二个 arg，可能暴露 ternary consumer 在 Call 位置参数的归属冲突。
    """
    SOURCE_CODE = """from typing import cast
x = cast(int, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
