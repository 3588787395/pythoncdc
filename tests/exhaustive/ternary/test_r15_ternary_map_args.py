import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryMapArgs(ExhaustiveTestCase):
    """Bug R15 (new): map(f, (a if c else b)) — map 双参数，第二是 parenthesized ternary。

    原始:
        map(f, (a if c else b))
    缺陷: ternary 作为 map 第二位置参数（带括号），f 作为第一位置参数。
         cond_block preload 含 PUSH_NULL + LOAD map + LOAD f，ternary merge
         块栈顶由 PRECALL + CALL 2 消费。R13 multi_arg_call_middle 已测
         f(0, ternary, 1) 中间 ternary 位置，R15 测 ternary 在末位变体。
    """
    SOURCE_CODE = """map(f, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
