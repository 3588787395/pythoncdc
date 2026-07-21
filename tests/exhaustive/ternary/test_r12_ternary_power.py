import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryPower(ExhaustiveTestCase):
    """Bug R12 (new): x ** (a if c else b) — BINARY_OP power 消费 ternary。

    原始:
        x = b ** (a if c else b)
    缺陷: ternary 作为 ** 的右操作数。merge_block 中 LOAD_NAME b +
         BINARY_OP 5 (oparg 5 对应 **) 消费 ternary 结果。R3/R6 已测过
         其他 binop，但 ** 的右结合性 + oparg=5 与其他 binop 不同。
    """
    SOURCE_CODE = """x = b ** (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
