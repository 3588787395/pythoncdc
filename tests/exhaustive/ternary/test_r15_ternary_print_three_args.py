import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryPrintThreeArgs(ExhaustiveTestCase):
    """Bug R15 (new): print((a if c else b), x, y) — print 三参数，首个是 parenthesized ternary。

    原始:
        print((a if c else b), x, y)
    缺陷: ternary 作为 print 第一个位置参数（带括号），后跟两个常量/变量参数。
         cond_block preload 含 PUSH_NULL + LOAD print，ternary merge 块栈顶与
         LOAD x + LOAD y 一起 PRECALL + CALL 3。R2 已测 print(a if cond else b)
         单 ternary 单参数，R4 已测 print(ternary, ternary) 双 ternary 双参数。
         R15 测 3 参数 + ternary 在首位 + 后续 sibling 是简单 Name 变体。
    """
    SOURCE_CODE = """print((a if c else b), x, y)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
