import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryForIterListMiddle(ExhaustiveTestCase):
    """Bug R14 (new): for x in [1, (a if c else b), 2]: pass — for iter 是 list 中间 ternary。

    原始:
        for x in [1, (a if c else b), 2]:
            pass
    缺陷: for 循环的 iter 表达式是 list literal，list 中间元素是 ternary。
         ternary merge 块栈顶先与 LOAD_CONST 1 + LOAD_CONST 2 一起 BUILD_LIST 3
         合成 List，再由 GET_ITER + FOR_ITER 消费。R2/R8 已测 for_iter_ternary
         (整个 iter 是 ternary)。R14 测 for iter list + ternary 中间元素变体：
         BUILD_LIST 3 + ternary + sibling 元素共存场景，参考 R13-08 list_middle_elem
         修复，但 R14 在 for 循环消费链下能否正确归约待验证。
    """
    SOURCE_CODE = """for x in [1, (a if c else b), 2]:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
