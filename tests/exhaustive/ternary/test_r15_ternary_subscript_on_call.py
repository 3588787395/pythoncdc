import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernarySubscriptOnCall(ExhaustiveTestCase):
    """Bug R15 (new): vars()[(a if c else b)] — subscript on call result with ternary index。

    原始:
        vars()[(a if c else b)]
    缺陷: ternary 作为 subscript 索引，被 subscript 的对象是 vars() 调用结果。
         cond_block preload 含 PUSH_NULL + LOAD vars + PRECALL + CALL 0，
         ternary merge 块栈顶作为 BINARY_SUBSCR 的索引。
    """
    SOURCE_CODE = """vars()[(a if c else b)]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
