import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryAsyncReturnWithBinop(ExhaustiveTestCase):
    """Bug R14 (new): async def f(): return (a if c else b) + 1 — async return ternary + binop。

    原始:
        async def f():
            return (a if c else b) + 1
    缺陷: async 函数中 return 表达式是 ternary + binop。R3 return_arith_mul 已测
         同步 return ternary + binop。R14 测 async 变体：async 函数的 RETURN_VALUE
         在 async 函数 code object 中，ternary merge 之后 BINARY_OP + RETURN_VALUE
         消费链。
    """
    SOURCE_CODE = """async def f():
    return (a if c else b) + 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
