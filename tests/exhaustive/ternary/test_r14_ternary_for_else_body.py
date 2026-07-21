import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryForElseBody(ExhaustiveTestCase):
    """Bug R14 (new): for else: y = (a if c else b) — for-else 体含 ternary。

    原始:
        for x in [1, 2, 3]:
            pass
        else:
            y = (a if c else b)
    缺陷: for 循环的 else 块体含 ternary 赋值。R7 for_else 测过 for-else + ternary
         在 cond 中。R14 测 for-else body 内 ternary 赋值变体：for 循环 polling
         结束后 POP_BLOCK + JUMP_FORWARD 到 else 块，ternary region 在 else 块
         入口可能与 for-loop region 边界冲突。
    """
    SOURCE_CODE = """for x in [1, 2, 3]:
    pass
else:
    y = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
