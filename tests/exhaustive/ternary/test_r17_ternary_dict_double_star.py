import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryDictDoubleStar(ExhaustiveTestCase):
    """Bug R17-05: x = {**d, **(a if c else b)} — dict double-star with ternary as second。

    原始:
        x = {**d, **(a if c else b)}
    缺陷: dict literal 含两个 **-unpacking，第二个是 ternary。R12 dict_merge_double_star
         已测过单元素 {**(a if c else b)}，但双 **-unpack 中第二个为 ternary 时，
         cond_block preload 的 BUILD_MAP 0 + 第一个 DICT_UPDATE + ternary merge
         的 DICT_UPDATE 1 协调失败，字节码指令数不匹配 (11 vs 9)。
    """
    SOURCE_CODE = """x = {**d, **(a if c else b)}
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
