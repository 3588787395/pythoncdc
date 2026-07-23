import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryYieldFromBinopTwo(ExhaustiveTestCase):
    """Bug R20-11: yield from (a if c else b) + (d if e else f) — yield from binop(两 ternary)。

    原始:
        def f():
            yield from (a if c else b) + (d if e else f)
    缺陷: yield from 的表达式是两个 ternary 的 BINARY_OP (+) 组合。R7/R13
         yield_from 测过 yield from (ternary) (单一 ternary 直接作 yield from
         目标)。本用例 yield from (ternary + ternary)：第一个 ternary merge 块
         栈顶 + 第二个 ternary merge 块栈顶 + BINARY_OP + GET_YIELD_FROM_ITER +
         SEND 循环。反编译把第一个 ternary 拆成独立语句 `(a if c else b)`，
         yield from 只保留第二个 ternary，丢失 BINARY_OP 与第一个 ternary 的
         栈关联，指令6操作码不匹配: LOAD_GLOBAL vs POP_TOP。
    """
    SOURCE_CODE = """def f():
    yield from (a if c else b) + (d if e else f)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
