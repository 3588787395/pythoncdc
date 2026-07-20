import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1TernaryInWith(ExhaustiveTestCase):
    """Bug 15: with (ternary) as f — with 上下文管理器中的 ternary 字节码不一致。

    原始:
        with (open(f1) if cond else open(f2)) as f:
            pass
    错误反编译: 字节码指令数 34 vs 39，with 语句的 ternary 上下文管理器
         未被正确重组。
    缺陷: with 语句的上下文管理器位置使用 ternary 表达式时，
         反编译器未能正确处理 BEFORE_WITH 与 __exit__ 调用顺序，
         重编字节码多出 5 条指令。IfExp 在 AST 中存在，
         但模块字节码不一致。
    """
    SOURCE_CODE = """with (open(f1) if cond else open(f2)) as f:
    pass"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
