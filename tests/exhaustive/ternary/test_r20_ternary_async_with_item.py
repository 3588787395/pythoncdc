import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryAsyncWithItem(ExhaustiveTestCase):
    """Bug R20-15: async with (a if c else b) as x — ternary 作 async with 的上下文管理器表达式。

    原始:
        async def f():
            async with (a if c else b) as x:
                pass
    缺陷: async with 的上下文管理器表达式（with item）是 ternary。R7 in_async_with
         测过 async with ctx: (ternary in body) (ternary 在 with body 内赋值)。
         本用例 ternary 是 with item 本身：BEFORE_ASYNC_WITH 消费 ternary merge
         块栈顶 + GET_AWAITABLE + SEND 轮询 + STORE_FAST x (as-target)。反编译
         退化为 `async with context() as x: pass`，用占位符 context() 替换 ternary，
         嵌套 code object 指令3参数不匹配: c vs context (op=LOAD_GLOBAL)。
    """
    SOURCE_CODE = """async def f():
    async with (a if c else b) as x:
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
