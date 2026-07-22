import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryMatrixMul(ExhaustiveTestCase):
    """Bug R12 (new): x @ (a if c else b) — BINARY_OP matrix mul 消费 ternary。

    原始:
        x = m @ (a if c else b)
    缺陷: ternary 作为矩阵乘法 @ 的右操作数。merge_block 中 LOAD_NAME m +
         BINARY_OP 22 (oparg 22 对应 @) 消费 ternary 结果。R3/R6 已测过其他
         binop，但 @ 是相对新的 op（PEP 465），oparg=22 (+=13 * 2 + 0)
         与其他 binop 不同。可能暴露 BINARY_OP arg 解码错误。
    """
    SOURCE_CODE = """x = m @ (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
