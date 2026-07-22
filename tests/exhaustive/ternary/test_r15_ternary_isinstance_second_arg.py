import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryIsinstanceSecondArg(ExhaustiveTestCase):
    """Bug R15 (new): isinstance(x, (a if c else b)) — isinstance 第二参数 ternary。

    原始:
        isinstance(x, (a if c else b))
    缺陷: ternary 作为 isinstance 第二位置参数（带括号），x 作为第一位置参数。
         cond_block preload 含 PUSH_NULL + LOAD isinstance + LOAD x，ternary
         merge 块栈顶由 PRECALL + CALL 2 消费。R13 multi_arg_call_middle 测过
         f(0, ternary, 1) 中间 ternary 位置，R15 测末位 ternary + isinstance。
    """
    SOURCE_CODE = """isinstance(x, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
