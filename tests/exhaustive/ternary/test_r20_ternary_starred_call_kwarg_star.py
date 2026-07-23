import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryStarredCallKwargStar(ExhaustiveTestCase):
    """Bug R20-14: f(x=1, *[a if c else b]) — kwarg + starred-list-ternary 混合 call。

    原始:
        f(x=1, *[a if c else b])
    缺陷: 函数调用同时含 kwarg (x=1) 与 starred 展开含 ternary 的 list literal
         [ternary]。R18 starred_call_with_pos_arg 测过 f(*(ternary), other)
         (starred-ternary + pos arg，无 kwarg)。本用例 kwarg + starred-list-ternary：
         CALL_FUNCTION_EX 路径需 BUILD_MAP (kwarg) + BUILD_LIST (starred list 含
         ternary) + LIST_EXTEND + CALL_FUNCTION_EX。反编译退化为
         `f(a if c else b, x=1)` (走 KW_NAMES+PRECALL+CALL 而非 CALL_FUNCTION_EX)，
         丢失 BUILD_LIST/LIST_EXTEND/BUILD_MAP/CALL_FUNCTION_EX，指令数不匹配 (14 vs 13)。
    """
    SOURCE_CODE = """f(x=1, *[a if c else b])
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
