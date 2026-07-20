import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryAugAssign(ExhaustiveTestCase):
    """Bug R6: ternary 在 augmented assignment 中 — 字节码不一致。

    原始: x += a if c else b
    缺陷: augmented assignment (x += ...) 在字节码中产生 LOAD_NAME x +
         LOAD (ternary result) + INPLACE_ADD + STORE_NAME x 序列。期望
         ternary merge 块识别 INPLACE_ADD + STORE 链；当前疑似未识别
         INPLACE_ADD wrapping，回退到 Expr(ternary)。
    """
    SOURCE_CODE = """x += a if c else b"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
