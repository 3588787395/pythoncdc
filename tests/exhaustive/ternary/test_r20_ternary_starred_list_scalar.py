import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryStarredListScalar(ExhaustiveTestCase):
    """Bug R20-04: x = [*[a if c else b]] — starred 展开含标量 ternary 的 list literal。

    原始:
        x = [*[a if c else b]]
    缺陷: 外层 list literal 通过 * 展开一个内层 list literal [ternary]，内层
         list 的元素是标量 ternary (a if c else b)。R1 starred 测过
         x = [*(items if cond else [])] (ternary 直接产出可迭代对象，无内层
         BUILD_LIST 包装)。本用例 ternary 产出标量，需 BUILD_LIST 1 包装成
         [ternary] 再 LIST_EXTEND 展开到外层 list。反编译丢失内层 BUILD_LIST
         与 LIST_EXTEND，退化为 `x = [a if c else b]`，指令数不匹配 (10 vs 8)。
    """
    SOURCE_CODE = """x = [*[a if c else b]]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
