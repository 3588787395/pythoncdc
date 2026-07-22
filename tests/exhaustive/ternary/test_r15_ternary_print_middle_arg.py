import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryPrintMiddleArg(ExhaustiveTestCase):
    """Bug R15 (new): print(x, (a if c else b), y) — print 三参数 ternary 在中间。

    原始:
        print(x, (a if c else b), y)
    缺陷: ternary 作为 print 第二位置参数（中间），前后是 x 和 y。
         cond_block preload 含 PUSH_NULL + LOAD print + LOAD x，ternary
         merge 块栈顶与 LOAD y 一起 PRECALL + CALL 3 消费。
         R13 multi_arg_call_middle 测过 f(0, ternary, 1) 通用 Call，
         R15 测 print 内置 + ternary 在中间变体。
    """
    SOURCE_CODE = """print(x, (a if c else b), y)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
