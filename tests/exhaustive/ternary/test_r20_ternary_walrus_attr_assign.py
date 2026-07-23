import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryWalrusAttrAssign(ExhaustiveTestCase):
    """Bug R20-03: obj.attr = (n := a if c else b) — walrus(ternary) 作属性赋值 RHS。

    原始:
        obj.attr = (n := a if c else b)
    缺陷: 属性赋值 obj.attr = RHS 的 RHS 是 walrus(ternary)。R8 walrus_assign
         测过 (n := (ternary)) 作为表达式语句。本用例 walrus(ternary) 是
         STORE_ATTR 的 value：LOAD obj + (ternary merge 块 COPY+STORE n) +
         STORE_ATTR attr。反编译退化为 `n = (a if c else b)` + `obj.attr = None`，
         walrus 的 COPY 被误识为独立 STORE，丢失 value 与 obj 的栈关联，
         指令4操作码不匹配: COPY vs STORE_NAME。
    """
    SOURCE_CODE = """obj.attr = (n := a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
