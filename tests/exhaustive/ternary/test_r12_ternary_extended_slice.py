import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryExtendedSlice(ExhaustiveTestCase):
    """Bug R12 (new): x[a:b, c if d else e] — extended slice 内 ternary。

    原始:
        r = x[a:b, c if d else e]
    缺陷: ternary 在 extended slice（多维下标）的某个维度。BUILD_TUPLE 2
         消费 a:b (BUILD_SLICE) 与 ternary 结果作为 slice tuple。merge_block
         含 BUILD_TUPLE 2 + BINARY_SUBSCR。R5 已测 ternary in subscript_slice
         （单维 a:b 形式），R12 测多维 extended slice 含 ternary 变体。
    """
    SOURCE_CODE = """r = x[a:b, c if d else e]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
