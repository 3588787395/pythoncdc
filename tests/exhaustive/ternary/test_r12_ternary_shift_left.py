import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryShiftLeft(ExhaustiveTestCase):
    """Bug R12 (new): x << (a if c else b) — BINARY_OP shift left 消费 ternary。

    原始:
        x = b << (a if c else b)
    缺陷: ternary 作为 << 的右操作数。merge_block 中 LOAD_NAME b +
         BINARY_OP 10 (oparg 10 对应 <<) 消费 ternary 结果。
    """
    SOURCE_CODE = """x = b << (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
