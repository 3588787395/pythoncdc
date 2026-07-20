import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryWhileCondBreak(ExhaustiveTestCase):
    """Bug R5-07: ternary 作为 while 条件 + 循环体内 break — 字节码不一致。

    原始:
        while (a if c else b):
            if x:
                break
    缺陷: R4-10 已识别为已知限制。R5 在 while(ternary) 基础上加入嵌套 if-break，
         加重控制流复杂度。期望：while 的 condition 表达式应包含 IfExp，
         当前疑似退化为 if + while + continue 结构（与 R4-10 同根因）。
    """
    SOURCE_CODE = """while (a if c else b):
    if x:
        break
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
