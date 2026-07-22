import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInList(ExhaustiveTestCase):
    """Bug R2-16: ternary 作为 list 字面量元素 — 字节码不一致。

    原始: l = [a if cond else b, c]
    缺陷: ternary 在 list 字面量中时，BUILD_LIST 在 merge_block 中消费
         ternary 结果与其他元素。反编译器可能丢失 BUILD_LIST 结构。
    """
    SOURCE_CODE = """l = [a if cond else b, c]"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
