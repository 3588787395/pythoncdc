import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernaryAttrAugAssign(ExhaustiveTestCase):
    """Bug R16 (new): (a if c else b).attr += 1 — ternary as aug assign attr obj。

    原始:
        (a if c else b).attr += 1
    缺陷: ternary 作为 augmented attribute assignment 的 base 对象。
         cond_block preload 无，ternary merge 块栈顶经 LOAD_ATTR attr
         + LOAD_CONST 1 + BINARY_OP + STORE_ATTR attr 消费链。
    """
    SOURCE_CODE = """(a if c else b).attr += 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
