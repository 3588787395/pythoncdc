import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryAwaitInCond(ExhaustiveTestCase):
    """Bug R17-10: async def f(): x = a if await g() else b — await in ternary condition。

    原始:
        async def f():
            x = a if await g() else b
    缺陷: ternary 的 condition 表达式是 await g()。cond_block 末尾的
         POP_JUMP_IF_FALSE 之前需要 GET_AWAITABLE + SEND 协程调度。R14
         await_with_binop 测过 await 与 ternary body 的组合，但 await 作为
         ternary condition 未覆盖。反编译完全丢失 ternary，退化为
         `await g()`，字节码指令数不匹配 (16 vs 14)。
    """
    SOURCE_CODE = """async def f():
    x = a if await g() else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
