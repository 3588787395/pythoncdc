import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernaryBodyAwaitMethod(ExhaustiveTestCase):
    """Bug R18-12: x = (await g() if c else b) — ternary body 是 await 调用。

    原始:
        async def f():
            x = (await g() if c else b)
    缺陷: ternary 的 true_value (body) 是 await g()。R17 await_in_cond 测过
         await 在 ternary 条件中，R14 await_attr_method 测过 await (ternary).m()。
         本用例 await 在 ternary body：true_value 块含 GET_AWAITABLE+SEND+
         YIELD_VALUE 协程调度轮询，与 ternary merge 块的 STORE_FAST x 归属冲突。
         反编译丢失 await 与 ternary，退化为 `x = b`，字节码指令数不匹配 (16 vs 9)。
    """
    SOURCE_CODE = """async def f():
    x = (await g() if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
