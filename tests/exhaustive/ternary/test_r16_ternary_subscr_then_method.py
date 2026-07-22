import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernarySubscrThenMethod(ExhaustiveTestCase):
    """Bug R16 (new): x[a if c else b].method() — ternary subscript + method chain。

    原始:
        x[a if c else b].method()
    缺陷: ternary 作为 BINARY_SUBSCR 的索引，subscript 结果再调用 .method()。
         cond_block preload 含 LOAD x，ternary merge 块栈顶经 BINARY_SUBSCR
         + LOAD_METHOD method + PRECALL + CALL 0 消费链。R15 subscript_chain
         测过 (ternary)[0][1]，R16 测 x[ternary].method() 链。
    """
    SOURCE_CODE = """x[a if c else b].method()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
