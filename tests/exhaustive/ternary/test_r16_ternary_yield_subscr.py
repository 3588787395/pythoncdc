import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernaryYieldSubscr(ExhaustiveTestCase):
    """Bug R16 (new): yield x[a if c else b] — yield subscript with ternary。

    原始:
        def gen():
            yield x[a if c else b]
    缺陷: yield 表达式的值是 x[ternary] subscript。ternary merge 块栈顶经
         BINARY_SUBSCR + YIELD_VALUE 消费链。R14 yield_with_binop 已测过
         yield (ternary + const)，R16 测 yield x[ternary] 变体。
    """
    SOURCE_CODE = """def gen():
    yield x[a if c else b]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
