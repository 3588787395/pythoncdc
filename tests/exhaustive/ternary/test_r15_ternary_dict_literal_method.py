import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryDictLiteralMethod(ExhaustiveTestCase):
    """Bug R15 (new): {}.get((a if c else b)) — dict literal obj.method。

    原始:
        {}.get((a if c else b))
    缺陷: ternary 作为 dict literal {}.get() 的参数。cond_block preload 含
         BUILD_MAP 0 + LOAD_METHOD get，ternary merge 块栈顶由 PRECALL +
         CALL 1 消费。R15 list_literal_method 测 list literal obj.method，
         本测试测 dict literal obj.method 变体。
    """
    SOURCE_CODE = """{}.get((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
