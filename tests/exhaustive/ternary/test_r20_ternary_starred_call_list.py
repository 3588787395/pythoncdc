import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryStarredCallList(ExhaustiveTestCase):
    """Bug R20-07: f(*[a if c else b]) — starred 展开含 ternary 的 list literal 进 call *args。

    原始:
        f(*[a if c else b])
    缺陷: 函数调用 *args 是 starred 展开一个含标量 ternary 的 list literal
         [ternary]。R8 starred_call 测过 f(*(a if c else b)) (ternary 直接
         产出可迭代对象被 unpack，无内层 BUILD_LIST 包装)。本用例 ternary 产出
         标量，需 BUILD_LIST 1 包装成 [ternary] 再 CALL_FUNCTION_EX unpack。
         反编译退化为 `f(a if c else b)` (走 PRECALL+CALL 而非
         CALL_FUNCTION_EX)，丢失 BUILD_LIST/CALL_FUNCTION_EX，指令6操作码
         不匹配: BUILD_LIST vs PRECALL。
    """
    SOURCE_CODE = """f(*[a if c else b])
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
