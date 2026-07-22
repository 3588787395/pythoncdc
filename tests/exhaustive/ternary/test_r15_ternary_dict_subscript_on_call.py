import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryDictSubscriptOnCall(ExhaustiveTestCase):
    """Bug R15 (new): dict()[(a if c else b)] — subscript on dict() call result。

    原始:
        dict()[(a if c else b)]
    缺陷: ternary 作为 subscript 索引，被 subscript 的对象是 dict() 调用结果。
         cond_block preload 含 PUSH_NULL + LOAD dict + PRECALL + CALL 0，ternary
         merge 块栈顶作为 BINARY_SUBSCR 的索引。R15 subscript_on_call 测过
         vars()[ternary]，本测试测 dict() 变体（CALL 0 + BINARY_SUBSCR）。
    """
    SOURCE_CODE = """dict()[(a if c else b)]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
