import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryTupleUnpackOneTernary(ExhaustiveTestCase):
    """Bug R19-06: x, y = c, (ternary) — tuple unpack 仅一个元素为 ternary，另一为常量。

    原始:
        x, y = c, (a if d else b)
    缺陷: tuple unpack 赋值 RHS = (c, ternary)，仅第二个元素是 ternary，第一个
         是简单 Name c。R6 unpack_assign 测过 `x, y = (t1), (t2)` (两元素均 ternary)，
         R13 tuple_swap 测过 `x, y = (t1), (t2)` (两元素均 ternary)。本用例仅一个
         ternary 元素 + 一个常量元素：BUILD_TUPLE 2 (在 ternary merge 块之后) +
         UNPACK_SEQUENCE 2 + STORE_NAME x + STORE_NAME y 消费链中，常量 c 的
         LOAD_NAME 与 ternary merge 块归属未协调，反编译退化为 `x = c`，丢失
         ternary 与第二目标 y。
    """
    SOURCE_CODE = """x, y = c, (a if d else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
