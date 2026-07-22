import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInTryElse(ExhaustiveTestCase):
    """Bug R7: try-except-else 中 else 块 ternary 赋值 — 字节码不一致。

    原始:
        try:
            pass
        except E:
            pass
        else:
            y = a if c else b
    缺陷: try-except-else 结构中，else 块在 try 块无异常时执行，
         其中包含 ternary 赋值。期望 else 块中的 ternary 正确归约为
         IfExp 赋值；当前疑似 try-else 的出口块（异常跳转表 + else 入口
         的 JUMP_FORWARD）与 ternary entry/merge 块共享导致归属冲突。
         R6 已修复 try body 与 except handler 内的 ternary (R6-06)，
         R7 测 else 块内的 ternary 以覆盖 try 结构的第 3 个分支。
    """
    SOURCE_CODE = """try:
    pass
except E:
    pass
else:
    y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
