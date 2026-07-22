import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInFinally(ExhaustiveTestCase):
    """Bug R7: finally 块中 ternary 赋值 — 字节码不一致。

    原始:
        try:
            pass
        finally:
            y = a if c else b
    缺陷: try-finally 结构中，finally 块包含 ternary 赋值。finally 块
         在 try 块正常/异常退出时都执行，其入口由 POP_EXCEPT/RERAISE
         路径触发。期望 finally 块中的 ternary 正确归约为 IfExp 赋值；
         当前疑似 finally 块的入口（异常清理路径）与 ternary entry 块
         共享导致归属冲突。
    """
    SOURCE_CODE = """try:
    pass
finally:
    y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
