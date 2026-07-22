import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryYieldFromAssign(ExhaustiveTestCase):
    """Bug R8: yield from (ternary) + 赋值 — 字节码不一致。

    原始:
        def g():
            x = yield from (a if c else b)
    缺陷: 生成器函数中 yield from (ternary) + 赋值。R7 已测过
         yield_from_ternary (yield from 在 ternary body)。
         R8 测 yield from (ternary) + 赋值变体：ternary merge 块
         作为 GET_YIELD_FROM_ITER 的源，与 STORE x 的 polling 循环
         路径可能冲突。
    """
    SOURCE_CODE = """def g():
    x = yield from (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
