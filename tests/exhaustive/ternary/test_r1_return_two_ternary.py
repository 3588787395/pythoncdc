import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1ReturnTwoTernary(ExhaustiveTestCase):
    """Bug 17: return (ternary, ternary) — 双 ternary 元组 return 字节码不一致。

    原始:
        def f():
            return (a if a > 0 else 0), (b if b > 0 else 0)
    错误反编译: 嵌套 code object 字节码 13 vs 15，多出 2 条指令。
    缺陷: return 语句的 tuple 包含两个 ternary 表达式，
         反编译器在嵌套函数 code object 中未能正确重组双 ternary
         求值路径，重编字节码多出 2 条 POP_TOP/LOAD_CONST 指令。
         IfExp 在 AST 中存在，但函数字节码不一致。
    """
    SOURCE_CODE = """def f():
    return (a if a > 0 else 0), (b if b > 0 else 0)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
