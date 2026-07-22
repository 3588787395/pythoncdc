import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryYieldFrom(ExhaustiveTestCase):
    """Bug R13 (new): yield from (a if c else b) — ternary as yield from expr。

    原始:
        def f():
            yield from (a if c else b)
    缺陷: ternary 作为 yield from 表达式。yield from 编译为 GET_YIELD_FROM_ITER
         + LOAD + SEND + YIELD_VALUE 等复杂指令。ternary merge 块栈输出作为
         yield from 的目标。R3 已测 ternary_yield 单纯 yield 场景，R4 已测
         ternary_in_yield_from。R13 重测 yield from 确认 R12 修复无退化。
    """
    SOURCE_CODE = """def f():
    yield from (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
