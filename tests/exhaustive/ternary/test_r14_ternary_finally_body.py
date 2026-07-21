import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryFinallyBody(ExhaustiveTestCase):
    """Bug R14 (new): finally: x = (a if c else b) — finally 体含 ternary。

    原始:
        try:
            pass
        finally:
            x = (a if c else b)
    缺陷: try-finally 块的 finally 体含 ternary 赋值。R7 finally 测过 try-finally
         + ternary。R14 重测确认 R13 修复无退化，并测 finally body 内 ternary 直接
         赋值变体：try 块结束（无论是否异常）后 POP_BLOCK 到 finally 块，ternary
         region 在 finally 块入口可能与 try-finally region 边界冲突。
    """
    SOURCE_CODE = """try:
    pass
finally:
    x = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
