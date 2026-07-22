import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryListMiddleElem(ExhaustiveTestCase):
    """Bug R13 (new): [1, (a if c else b), 2] — ternary as middle element in list literal。

    原始:
        [1, (a if c else b), 2]
    缺陷: ternary 作为 list literal 的中间元素。BUILD_LIST 3 指令消费 3 个栈项
         （LOAD_CONST 1, ternary merge, LOAD_CONST 2）。R2 已测 ternary_in_list
         单纯场景（test_r2_ternary_in_list）。R13 测 list 多元素 + ternary 在中间
         位置的变体（验证 ternary merge 在 BUILD_LIST 多元素场景的归约）。
    """
    SOURCE_CODE = """[1, (a if c else b), 2]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
