import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryAsyncWithMultiAs(ExhaustiveTestCase):
    """Bug R9: async with 多个 as target + body ternary — 字节码不一致。

    原始:
        async def f():
            async with a as x, b as y:
                z = c if cond else d
    缺陷: R7-03/R8 已知 async with 单 as body ternary 失败。R9 测多个
         as target 变体：两个 as_target 的 STORE_FAST x/y 与 ternary
         merge 块的 STORE_FAST z 在同一 with body 路径，且 async with
         的多个 BEFORE_ASYNC_WITH + GET_AWAITABLE + SEND polling 路径
         嵌套，可能暴露 as_target 顺序推断与归属冲突。
    """
    SOURCE_CODE = """async def f():
    async with a as x, b as y:
        z = c if cond else d
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
