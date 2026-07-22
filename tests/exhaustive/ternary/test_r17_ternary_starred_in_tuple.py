import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryStarredInTuple(ExhaustiveTestCase):
    """Bug R17-09: x = (1, *(a if c else b), 2) — starred ternary in tuple middle。

    原始:
        x = (1, *(a if c else b), 2)
    缺陷: tuple literal 中间位置含 *-starred ternary。BUILD_TUPLE 在 ternary
         merge 块前后分两段（前段 LOAD_CONST 1，后段 LOAD_CONST 2），LIST_EXTEND
         消费 ternary 结果。R2 ternary_in_starred 测过 *y, = (a if c else b)
         （unpack target），R13 starred_assign 测过 *y, = (a if c else b)，但
         tuple 中间 *-starred ternary 未覆盖，字节码指令数不匹配 (13 vs 12)。
    """
    SOURCE_CODE = """x = (1, *(a if c else b), 2)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
