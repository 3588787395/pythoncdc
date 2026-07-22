import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernarySubscrAugAssign(ExhaustiveTestCase):
    """Bug R16 (new): x[a if c else b] += 1 — ternary as aug assign subscript index。

    原始:
        x[a if c else b] += 1
    缺陷: ternary 作为 augmented subscript assignment 的索引。
         cond_block preload 含 LOAD x，ternary merge 块栈顶经
         BINARY_SUBSCR + LOAD_CONST 1 + BINARY_OP + STORE_SUBSCR 消费链。
    """
    SOURCE_CODE = """x[a if c else b] += 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
