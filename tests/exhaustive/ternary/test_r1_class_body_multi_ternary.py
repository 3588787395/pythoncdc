import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1ClassBodyMultiTernary(ExhaustiveTestCase):
    """Bug 16: class body 含多个 ternary 属性 — 嵌套 code object 字节码不一致。

    原始:
        class C:
            x = a if a > 0 else 0
            y = b if b > 0 else 0
    错误反编译:
        class C:
            x = (a if a > 0 else 0)
            (b > 0)
            y = (b if b > 0 else 0)
    缺陷: class 体内多个 ternary 赋值时，反编译器在第二个 ternary 之前
         多输出了一行 `(b > 0)` 表达式语句（条件被泄漏到外层），
         重编字节码多出 4 条指令。IfExp 在 AST 中存在，
         但 class code object 字节码不一致。
    """
    SOURCE_CODE = """class C:
    x = a if a > 0 else 0
    y = b if b > 0 else 0"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
