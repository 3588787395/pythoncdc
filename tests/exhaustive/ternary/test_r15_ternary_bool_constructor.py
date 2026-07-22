import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryBoolConstructor(ExhaustiveTestCase):
    """Bug R15 (new): bool((a if c else b)) — bool constructor 单 ternary 参数。

    原始:
        bool((a if c else b))
    缺陷: ternary 作为内置 bool() 的单参数（带括号）。cond_block preload 含
         PUSH_NULL + LOAD bool，ternary merge 块栈顶由 PRECALL + CALL 1 消费。
    """
    SOURCE_CODE = """bool((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
