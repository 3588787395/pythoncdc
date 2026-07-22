import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryTupleLiteralMethod(ExhaustiveTestCase):
    """Bug R15 (new): ().count((a if c else b)) — tuple literal obj.method。

    原始:
        ().count((a if c else b))
    缺陷: ternary 作为 tuple literal ().count() 的参数。cond_block preload 含
         BUILD_TUPLE 0 + LOAD_METHOD count，ternary merge 块栈顶由 PRECALL +
         CALL 1 消费。R15 list_literal_method 测 list literal，本测试测 tuple
         literal 变体。
    """
    SOURCE_CODE = """().count((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
