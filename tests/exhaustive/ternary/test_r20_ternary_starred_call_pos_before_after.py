import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryStarredCallPosBeforeAfter(ExhaustiveTestCase):
    """Bug R20-08: f(1, *[a if c else b], 2) — pos arg 在 starred-list-ternary 前后。

    原始:
        f(1, *[a if c else b], 2)
    缺陷: 函数调用含位置参数 1 (在 starred 之前) + starred 展开含 ternary 的
         list literal [ternary] + 位置参数 2 (在 starred 之后)。R18
         starred_call_with_pos_arg 测过 f(*(a if c else b), other) (starred
         ternary 在前，单个 pos arg 在后，且 starred 是直接 ternary 非 list)。
         本用例 pos arg 在 starred 前后均有，且 starred 是 list literal 含 ternary：
         BUILD_LIST 0 + LOAD_CONST 1 + LIST_APPEND + (ternary merge 块) +
         BUILD_LIST 1 + LIST_EXTEND + LOAD_CONST 2 + LIST_APPEND + LIST_TO_TUPLE
         + CALL_FUNCTION_EX。反编译退化为 `f(1, a if c else b, 2)` (走
         PRECALL+CALL)，丢失 BUILD_LIST/LIST_EXTEND/LIST_APPEND/LIST_TO_TUPLE/
         CALL_FUNCTION_EX，指令数不匹配 (17 vs 13)。
    """
    SOURCE_CODE = """f(1, *[a if c else b], 2)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
