import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInKwarg(ExhaustiveTestCase):
    """Bug R2-9: ternary 作为函数调用关键字参数值 — 字节码不一致。

    原始: func(key=a if cond else b)
    缺陷: ternary 作为关键字参数值时，KW_NAMES/KW_DICT 在 merge_block 中
         消费 ternary 结果。反编译器可能丢失关键字参数结构。
    """
    SOURCE_CODE = """func(key=a if cond else b)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
