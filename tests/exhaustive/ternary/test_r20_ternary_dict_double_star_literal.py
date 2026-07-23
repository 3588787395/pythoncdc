import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryDictDoubleStarLiteral(ExhaustiveTestCase):
    """Bug R20-06: x = {**{a if c else b: 1}} — dict double-star 展开含 ternary key 的 dict literal。

    原始:
        x = {**{a if c else b: 1}}
    缺陷: 外层 dict literal 通过 ** 展开一个内层 dict literal {ternary: 1}，
         内层 dict 的 key 是 ternary。R17 dict_double_star 测过
         x = {**d, **(a if c else b)} (ternary 直接产出被展开的 dict，无内层
         BUILD_MAP 包装)。本用例 ternary 是内层 dict 的 key：BUILD_MAP 0 (外层)
         + (ternary merge 块) + LOAD_CONST 1 + BUILD_MAP 1 (内层 dict 消费
         ternary key) + DICT_UPDATE (展开内层到外层)。反编译退化为
         `x = {a if c else b: 1}`，丢失外层 BUILD_MAP/DICT_UPDATE，指令数不匹配 (11 vs 9)。
    """
    SOURCE_CODE = """x = {**{a if c else b: 1}}
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
