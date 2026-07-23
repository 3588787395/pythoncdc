import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryTupleUnpackMiddleTernary(ExhaustiveTestCase):
    """Bug R19-07: a, b, c = 1, (ternary), 2 — ternary 位于 tuple unpack 中间位置。

    原始:
        a, b, c = 1, (x if d else y), 2
    缺陷: tuple unpack 赋值 RHS = (1, ternary, 2)，三个元素中中间是 ternary，
         前后均为常量。R6/R13 unpack 测过两元素均 ternary。本用例三目标 unpack
         中 ternary 在中间：BUILD_TUPLE 3 (在 ternary merge 块之后) +
         UNPACK_SEQUENCE 3 + STORE_NAME a/b/c 消费链中，前置 LOAD_CONST 1 与
         后置 LOAD_CONST 2 协调失败，反编译退化为 `a = 2`，丢失 ternary 与
         中间目标 b、首元素 1。
    """
    SOURCE_CODE = """a, b, c = 1, (x if d else y), 2
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
