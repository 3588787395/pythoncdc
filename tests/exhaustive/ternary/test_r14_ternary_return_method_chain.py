import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryReturnMethodChain(ExhaustiveTestCase):
    """Bug R14 (new): return (a if c else b).method() — return ternary 后接 method call。

    原始:
        def f():
            return (a if c else b).method()
    缺陷: ternary 作为 return 表达式的 receiver，再链式 LOAD_METHOD method +
         PRECALL + CALL。R3 已测过 return_call (return ternary call)。R13-01
         修复了 string method chain + ternary arg 场景。R14 测 return ternary +
         method 链变体：ternary merge 之后 LOAD_METHOD method + PRECALL + CALL
         消费链作为 RETURN_VALUE 栈顶。
    """
    SOURCE_CODE = """def f():
    return (a if c else b).method()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
