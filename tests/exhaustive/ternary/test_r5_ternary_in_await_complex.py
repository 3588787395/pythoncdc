import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInAwaitComplex(ExhaustiveTestCase):
    """Bug R5-22: async 函数 return await (ternary) — 字节码不一致。

    原始:
        async def f():
            return await (a if c else b)
    缺陷: ternary 作为 await 表达式且整体被 return 消费时，merge_block 同时含
         GET_AWAITABLE + SEND + RETURN_VALUE。R4-02 已通过简单 await 场景
         （test_r4_ternary_await_expr，无 return）。R5 用 return await (ternary)
         复合形式重测，分离 return + await + ternary 三层结构根因。
         期望：Return(Await(IfExp)) 正确归约。
    """
    SOURCE_CODE = """async def f():
    return await (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
