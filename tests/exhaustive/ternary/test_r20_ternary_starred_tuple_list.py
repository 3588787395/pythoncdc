import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryStarredTupleList(ExhaustiveTestCase):
    """Bug R20-05: x = (*[a if c else b],) — starred 展开含 ternary 的 list 进 tuple。

    原始:
        x = (*[a if c else b],)
    缺陷: tuple literal (*[ternary],) 通过 * 展开一个含标量 ternary 的 list
         literal [ternary]。R2 ternary_in_tuple 测过 (ternary,) (ternary 直接
         作 tuple 元素，无 starred 展开)。本用例 starred + 内层 BUILD_LIST +
         LIST_EXTEND + LIST_TO_TUPLE 消费链：ternary merge 块栈顶先被
         BUILD_LIST 1 包装，再 LIST_EXTEND 展开到外层 tuple builder，最后
         LIST_TO_TUPLE。反编译退化为 `x = (a if c else b,)`，丢失 BUILD_LIST/
         LIST_EXTEND/LIST_TO_TUPLE，指令数不匹配 (11 vs 8)。
    """
    SOURCE_CODE = """x = (*[a if c else b],)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
