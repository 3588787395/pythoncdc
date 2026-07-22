import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryWhileElseTernary(ExhaustiveTestCase):
    """Bug R6: ternary 在 while-else 块中 — 字节码不一致。

    原始:
        while x:
            pass
        else:
            y = a if c else b
    缺陷: while-else 结构中，else 块包含 ternary 赋值。期望 else 块中的
         ternary 正确归约；当前疑似 while-else 的出口块与 ternary 的
         entry/merge 块共享导致归属冲突。
    """
    SOURCE_CODE = """while x:
    pass
else:
    y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
