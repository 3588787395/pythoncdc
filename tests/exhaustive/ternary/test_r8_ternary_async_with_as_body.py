import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryAsyncWithAsBody(ExhaustiveTestCase):
    """Bug R8: async with as + body ternary 赋值 — 字节码不一致。

    原始:
        async def f():
            async with ctx as x:
                y = a if c else b
    缺陷: async with-as 语句 body 中包含 ternary 赋值。R7-03 已知
         `async with ctx:` 无 as 变体失败。R8 测带 as 变体：as_target
         的 STORE_FAST x 与 ternary merge 块的 STORE_FAST y 在同一
         with body 路径，可能暴露 as_target 误推断或归属冲突。
    """
    SOURCE_CODE = """async def f():
    async with ctx as x:
        y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
