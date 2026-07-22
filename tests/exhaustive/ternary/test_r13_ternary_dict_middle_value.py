import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryDictMiddleValue(ExhaustiveTestCase):
    """Bug R13 (new): {1: x, 2: (a if c else b), 3: y} — ternary as middle dict value。

    原始:
        {1: x, 2: (a if c else b), 3: y}
    缺陷: ternary 作为 dict literal 的中间 value。BUILD_MAP 3 或 BUILD_CONST_KEY_MAP
         3 指令消费 3 个 value 栈项。LOAD_CONST keys tuple + 3 个 value（其中
         一个是 ternary merge 块栈输出）。R2 已测 ternary_in_dict 单元素场景，
         R4 测 ternary_in_dict_value。R13 测 dict 多元素 + ternary 在中间 value
         位置的变体（验证 ternary merge 在 BUILD_MAP 多元素场景的归约）。
    """
    SOURCE_CODE = """{1: x, 2: (a if c else b), 3: y}
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
