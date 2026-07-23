import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryWalrusSubscrAssign(ExhaustiveTestCase):
    """Bug R20-02: x[(n := a if c else b)] = y — walrus(ternary) 作 subscript 赋值目标（store）。

    原始:
        x[(n := a if c else b)] = y
    缺陷: STORE_SUBSCR 赋值目标的下标是 walrus(ternary)。R16 walrus_subscr_idx
         测过 x[(n := a if c else b)] (LOAD/BINARY_SUBSCR 消费，表达式语句)。
         本用例是 STORE 上下文：LOAD x + LOAD y + (walrus ternary merge 块
         COPY+STORE n) + STORE_SUBSCR，反编译退化为 `n = (a if c else b)`，
         丢失外层 LOAD x / LOAD y / STORE_SUBSCR，字节码指令数不匹配 (11 vs 7)。
    """
    SOURCE_CODE = """x[(n := a if c else b)] = y
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
