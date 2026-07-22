import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryListConstructor(ExhaustiveTestCase):
    """Bug R15 (new): list((a if c else b)) — list constructor 单 ternary 参数。

    原始:
        list((a if c else b))
    缺陷: ternary 作为内置 list() 的单参数（带括号）。cond_block preload 含
         PUSH_NULL + LOAD list，ternary merge 块栈顶由 PRECALL + CALL 1 消费。
    """
    SOURCE_CODE = """list((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
