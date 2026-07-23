import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernaryAwaitCallTernaryArg(ExhaustiveTestCase):
    """Bug R18-02: await g(a if c else b) — await 调用，参数为 ternary。

    原始:
        async def f():
            await g(a if c else b)
    缺陷: await 表达式消费一个函数调用 g(...)，而 g 的唯一位置参数是 ternary。
         R17 await_in_cond 测过 await 在 ternary 条件中，R14 await_attr_method
         测过 await (ternary).attr.method()。本用例 await 的操作数是「带 ternary
         参数的 Call」: ternary merge 块的 PRECALL+CALL 之后还需 GET_AWAITABLE +
         SEND + YIELD_VALUE 协程调度轮询循环。反编译完全丢失 ternary 参数与
         await 包装，退化为 `await g()`，字节码指令数不匹配 (17 vs 14)。
    """
    SOURCE_CODE = """async def f():
    await g(a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
