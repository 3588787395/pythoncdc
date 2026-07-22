import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInListcomp(ExhaustiveTestCase):
    """Bug R2-32: ternary 在 list comprehension 中 — 字节码不一致。

    原始: l = [x if cond else 0 for x in items]
    缺陷: ternary 在 listcomp element 中时，LIST_APPEND 在 merge_block 中消费
         ternary 结果。反编译器可能丢失 listcomp 结构。
    """
    SOURCE_CODE = """l = [x if cond else 0 for x in items]"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
