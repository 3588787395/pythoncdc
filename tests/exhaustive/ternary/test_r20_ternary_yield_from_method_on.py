import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryYieldFromMethodOn(ExhaustiveTestCase):
    """Bug R20-12: yield from (a if c else b).m() — yield from 方法调用 on ternary。

    原始:
        def f():
            yield from (a if c else b).m()
    缺陷: yield from 的表达式是 ternary 上的方法调用 (ternary).m()。R7/R13
         yield_from 测过 yield from (ternary) (单一 ternary 直接作 yield from
         目标)。本用例 yield from (ternary).m()：ternary merge 块栈顶 +
         LOAD_METHOD m + PRECALL + CALL + GET_YIELD_FROM_ITER + SEND 循环。
         反编译完全丢失 ternary 与方法调用，退化为 `def f(): None`，
         嵌套 code object 指令数严重不匹配 (17 vs 3)。
    """
    SOURCE_CODE = """def f():
    yield from (a if c else b).m()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
