import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryAsyncReturnWithAwait(ExhaustiveTestCase):
    """Bug R17-03: async def f(): return (a if c else b) + await g() — async return ternary+await。

    原始:
        async def f():
            return (a if c else b) + await g()
    缺陷: async function body 中 return 语句的值是 (ternary) + (await expr)
         复合表达式。ternary 的 merge 块需要消费 BINARY_OP 后再 RETURN_VALUE，
         但 await 表达式在 ternary 之外。反编译器完全丢失 return 值，退化为
         `return None`，字节码指令数严重不匹配 (16 vs 5)。
    """
    SOURCE_CODE = """async def f():
    return (a if c else b) + await g()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
