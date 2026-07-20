import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInAsyncWithAs(ExhaustiveTestCase):
    """Bug R7: async with as target + body ternary — 字节码不一致。

    原始:
        async def f():
            async with ctx as cm:
                y = a if c else b
    缺陷: async with 带 as cm 目标 + body ternary 赋值。R7-03 已测
         无 as 的 async with body ternary (as 被错误识别为 y)。
         R7 测带 as cm 的变体：as 目标 cm 与 body 内 ternary 的
         STORE_FAST y 不同，可能让 with region 的 as_target 推断
         与 ternary value_target 推断冲突。
    """
    SOURCE_CODE = """async def f():
    async with ctx as cm:
        y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
