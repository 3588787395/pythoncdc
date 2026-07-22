import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryAwaitAsyncWithCombo(ExhaustiveTestCase):
    """Bug R9: await ternary + async with body ternary 组合 — 字节码不一致。

    原始:
        async def f():
            x = await (g() if c else h())
            async with ctx as y:
                z = a if c2 else b
    缺陷: R7-03 已知 async with body ternary 失败。R9 测 await ternary
         与 async with body ternary 组合变体：await 的 SEND polling
         嵌套 ternary merge，与 async with 的 BEFORE_ASYNC_WITH +
         GET_AWAITABLE + SEND polling 在同一函数体内可能暴露 SEND 路径
         归属冲突。
    """
    SOURCE_CODE = """async def f():
    x = await (g() if c else h())
    async with ctx as y:
        z = a if c2 else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
