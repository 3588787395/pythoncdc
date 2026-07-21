import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryWithMultipleSecondAs(ExhaustiveTestCase):
    """Bug R14 (new): with a as x, (b if c else d) as y: pass — multi-with 第二个 item 是 ternary + as。

    原始:
        with a as x, (b if c else d) as y:
            pass
    缺陷: with 多 item，第二个 item 的 context manager 是 ternary 且带 as 别名。
         R3 with_as 测单 with ternary + as。R7 with_multiple 测 multi-with 中含
         ternary 但变体可能不完整。R14 测 multi-with 第二 item ternary + as 别名
         完整变体：BUILD_TUPLE 2 + WITH_EXCEPT_START + WITH_EXIT 等指令链与 ternary
         merge 块归属可能冲突。
    """
    SOURCE_CODE = """with a as x, (b if c else d) as y:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
