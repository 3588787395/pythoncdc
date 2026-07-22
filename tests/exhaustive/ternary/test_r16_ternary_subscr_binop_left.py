import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernarySubscrBinopLeft(ExhaustiveTestCase):
    """Bug R16 (new): x[(a if c else b) + 1] — ternary as binop left in subscript。

    原始:
        x[(a if c else b) + 1]
    缺陷: ternary 作为 subscript 索引的 binary op + 1 左操作数。
         cond_block preload 含 LOAD x，ternary merge 块栈顶经
         BINARY_OP + 1 + BINARY_SUBSCR 消费链。R4 in_subscript 已测过
         ternary 单独作 subscript 索引，R16 测 ternary + binop 复合。
    """
    SOURCE_CODE = """x[(a if c else b) + 1]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
