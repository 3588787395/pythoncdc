import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryTupleConstructor(ExhaustiveTestCase):
    """Bug R15 (new): tuple((a if c else b)) — tuple constructor 单 ternary 参数。

    原始:
        tuple((a if c else b))
    缺陷: ternary 作为内置 tuple() 的单参数（带括号）。cond_block preload 含
         PUSH_NULL + LOAD tuple，ternary merge 块栈顶由 PRECALL + CALL 1 消费。
    """
    SOURCE_CODE = """tuple((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
