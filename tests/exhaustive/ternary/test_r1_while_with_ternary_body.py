import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1WhileWithTernaryBody(ExhaustiveTestCase):
    """Bug 13: while 循环体含 ternary 赋值 — 字节码指令数不一致。

    原始:
        while cond:
            x = a if a > 0 else 0
    错误反编译: 字节码指令数 13 vs 15，while 体内 ternary 求值路径错乱。
    缺陷: while 循环体内嵌 ternary 赋值时，反编译器未能正确重组
         POP_JUMP_IF_FALSE/JUMP_FORWARD 跳转目标，导致重编字节码
         多出 2 条指令。IfExp 在 AST 中存在，但模块字节码不一致。
    """
    SOURCE_CODE = """while cond:
    x = a if a > 0 else 0"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
