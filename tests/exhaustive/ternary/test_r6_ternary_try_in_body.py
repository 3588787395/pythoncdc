import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryTryInBody(ExhaustiveTestCase):
    """Bug R6: ternary 在 try body 中 — 字节码不一致。

    原始:
        try:
            x = a if c else b
        except:
            pass
    缺陷: ternary 在 try body 中作为赋值表达式。期望 try 区域与 ternary
         区域正确归约；当前疑似 try 的异常处理 entry/exit 与 ternary 的
         merge 块共享导致归属冲突。
    """
    SOURCE_CODE = """try:
    x = a if c else b
except:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
