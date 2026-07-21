import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryContextlibSuppress(ExhaustiveTestCase):
    """Bug R11 (new): contextlib.suppress + ternary in with item.

    原始:
        from contextlib import suppress
        with suppress(E1 if c else E2):
            pass
    缺陷: ternary 作为 suppress() 的参数，整个 suppress(ternary) 作为 with
         上下文管理器。PUSH_NULL + LOAD_NAME suppress + ternary merge + PRECALL 1
         + CALL 1 + WITH + POP_TOP。ternary merge 块的栈输出作为 suppress Call
         的 arg，且 suppress Call 又作为 WITH 的上下文管理器。可能暴露
         ternary 嵌套在 Call 内 + Call 嵌套在 with 内的双重归属冲突。
    """
    SOURCE_CODE = """from contextlib import suppress
with suppress((E1 if c else E2)):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
