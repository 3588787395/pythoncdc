import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryTryInHandler(ExhaustiveTestCase):
    """Bug R6: ternary 在 except handler 中 — 字节码不一致。

    原始:
        try:
            pass
        except E:
            x = a if c else b
    缺陷: ternary 在 except handler body 中作为赋值。期望 except handler
         区域与 ternary 区域正确归约；当前疑似 except handler 的出口
         (POP_EXCEPT + RERAISE/JUMP_FORWARD) 与 ternary merge 块共享。
    """
    SOURCE_CODE = """try:
    pass
except E:
    x = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
