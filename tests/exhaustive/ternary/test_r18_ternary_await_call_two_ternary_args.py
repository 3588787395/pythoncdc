import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernaryAwaitCallTwoTernaryArgs(ExhaustiveTestCase):
    """Bug R18-03: await g(a if c else b, d if e else f) — await 调用，两个 ternary 参数。

    原始:
        async def f():
            await g(a if c else b, d if e else f)
    缺陷: await 表达式消费 g(...)，g 的两个位置参数都是 ternary。两个 ternary
         的 merge 块先后汇聚到同一 PRECALL+CALL，再被 GET_AWAITABLE+SEND
         协程调度消费。R18-02 测单 ternary 参数，本用例测双 ternary 参数：
         第二个 ternary 的 merge 块归属与第一个 ternary 的 merge 块协调失败，
         反编译退化为 `await g(a if c else b)` (丢失第二参数)，字节码指令数
         不匹配 (20 vs 15)。
    """
    SOURCE_CODE = """async def f():
    await g(a if c else b, d if e else f)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
