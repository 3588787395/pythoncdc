import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryPartialmethod(ExhaustiveTestCase):
    """Bug R10-12 (re-verify in R11): functools.partialmethod + ternary.

    原始:
        from functools import partialmethod
        class C:
            def _m(self, x):
                return x
            m = partialmethod(_m, (a if c else b))
    缺陷: partialmethod(_m, ternary) 在 class body 中作为属性赋值。
         partialmethod 调用栈帧 LOAD_NAME partialmethod + LOAD_NAME _m +
         ternary merge + PRECALL + CALL + STORE_NAME m。ternary merge 块的
         栈输出作为 partialmethod 第二个参数，可能暴露 ternary consumer 识别冲突。
    """
    SOURCE_CODE = """from functools import partialmethod
class C:
    def _m(self, x):
        return x
    m = partialmethod(_m, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
