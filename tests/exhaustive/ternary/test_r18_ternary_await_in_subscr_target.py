import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernaryAwaitInSubscrTarget(ExhaustiveTestCase):
    """Bug R18-06: x[(await y) if c else b] = 1 — subscript target 含 await+ternary。

    原始:
        async def f():
            x[(await y) if c else b] = 1
    缺陷: STORE_SUBSCR 的下标 target 是 ternary，且 ternary 的 true 值是
         await y (协程调度)。R16 await_with_binop 测过 await 与 binop 组合，
         R17 await_in_cond 测过 await 在 ternary 条件。本用例 await 在 ternary
         body 且整体作为 subscript target：ternary true_value 块含
         GET_AWAITABLE+SEND+YIELD_VALUE 轮询，与 ternary merge 块的 STORE_SUBSCR
         归属冲突。反编译丢失 await 与 ternary，字节码指令数不匹配 (16 vs 11)。
    """
    SOURCE_CODE = """async def f():
    x[(await y) if c else b] = 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
