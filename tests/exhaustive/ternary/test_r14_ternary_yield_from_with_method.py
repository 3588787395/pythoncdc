import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryYieldFromWithMethod(ExhaustiveTestCase):
    """Bug R14 (new): yield from (a if c else b).items() — yield from ternary with method chain。

    原始:
        def gen():
            yield from (a if c else b).items()
    缺陷: yield from 表达式是 ternary 后接 .items() 方法调用。R8 yield_from_assign
         已测 yield from (ternary) + 赋值。R13 yield_from 重测同步 yield from。
         R14 测 yield from ternary + method 链变体：ternary merge 之后 LOAD_METHOD
         items + PRECALL + CALL 0 消费链作为 GET_YIELD_FROM_ITER + SEND + YIELD_VALUE
         polling 循环输入。
    """
    SOURCE_CODE = """def gen():
    yield from (a if c else b).items()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
