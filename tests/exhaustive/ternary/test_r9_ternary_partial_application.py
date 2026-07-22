import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryPartialApplication(ExhaustiveTestCase):
    """Bug R9: partial 应用 + ternary — 字节码不一致。

    原始:
        from functools import partial
        f = partial(g, (a if c else b))
    缺陷: partial(g, ternary) 调用，ternary merge 块作为 partial
         的第二个参数。partial 调用栈帧 LOAD_NAME partial + LOAD_NAME g
         + ternary merge + PRECALL + CALL 与一般 call 不同，可能暴露
         ternary consumer 识别冲突。
    """
    SOURCE_CODE = """from functools import partial
f = partial(g, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
