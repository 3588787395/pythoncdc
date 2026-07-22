import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInTuple(ExhaustiveTestCase):
    """Bug R2-15: ternary 作为元组字面量元素 — 字节码不一致。

    原始: t = (a if cond else b, c)
    缺陷: ternary 在元组字面量中时，BUILD_TUPLE 在 merge_block 中消费
         ternary 结果与其他元素。反编译器可能丢失 BUILD_TUPLE 结构。
    """
    SOURCE_CODE = """t = (a if cond else b, c)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
