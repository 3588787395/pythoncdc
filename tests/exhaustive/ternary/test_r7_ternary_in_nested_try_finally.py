import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInNestedTryFinally(ExhaustiveTestCase):
    """Bug R7: 嵌套 try-finally 中内层 finally ternary — 字节码不一致。

    原始:
        try:
            try:
                pass
            finally:
                y = a if c else b
        except E:
            pass
    缺陷: 嵌套 try-finally，内层 finally 块包含 ternary 赋值，外层是
         try-except。R7-05 已测单层 try-finally + ternary in finally
         严重退化（try-finally 被反编译为 try-except）。R7 测嵌套变体
         暴露多层 POP_EXCEPT/RERAISE 链与 ternary merge 块的交互。
    """
    SOURCE_CODE = """try:
    try:
        pass
    finally:
        y = a if c else b
except E:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
