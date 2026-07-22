import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernarySubscriptOnTernary(ExhaustiveTestCase):
    """Bug R15 (new): (a if c else b)[0] — subscript on ternary with const index。

    原始:
        (a if c else b)[0]
    缺陷: ternary 作为被 subscript 的对象，索引是常量 0。ternary merge 块栈顶
         作为 BINARY_SUBSCR 的 obj，由 LOAD_CONST 0 + BINARY_SUBSCR 消费。
         验证 subscript on ternary result 变体。
    """
    SOURCE_CODE = """(a if c else b)[0]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
