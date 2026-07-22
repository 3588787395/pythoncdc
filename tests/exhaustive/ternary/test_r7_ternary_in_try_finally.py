import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInTryFinally(ExhaustiveTestCase):
    """Bug R7: try-finally body 中 ternary 赋值 — 字节码不一致。

    原始:
        try:
            y = a if c else b
        finally:
            pass
    缺陷: try-finally 结构（无 except）中，try body 包含 ternary 赋值。
         R6 已修复 try-except 的 try body 内 ternary（test_r6_ternary_try_in_body
         是 try-except 变体）。R7 测纯 try-finally（无 except）变体：
         纯 finally 的异常清理路径与 POP_EXCEPT 链与 except 不同，
         可能暴露新的归属冲突。
    """
    SOURCE_CODE = """try:
    y = a if c else b
finally:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
