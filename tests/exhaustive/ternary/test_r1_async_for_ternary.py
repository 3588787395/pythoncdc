import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1AsyncForTernary(ExhaustiveTestCase):
    """Bug 14: async for 体内 ternary 赋值 — body 退化为两个表达式语句。

    原始:
        async def f():
            async for i in g():
                x = i if i > 0 else 0
    错误反编译:
        async def f():
            async for i in g():
                i
                0
    缺陷: async for 体内 ternary 赋值未识别为 TERNARY 区域，
         body 被拆解为两个表达式语句 `i` 和 `0`，完全丢失
         IfExp 结构与外层 x 赋值绑定。IfExp AST 节点缺失，
         行为严重错误。
    """
    SOURCE_CODE = """async def f():
    async for i in g():
        x = i if i > 0 else 0"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
