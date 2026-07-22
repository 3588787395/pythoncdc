import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryDictMergeDoubleStar(ExhaustiveTestCase):
    """Bug R12 (new): {**(a if c else b)} — DICT_MERGE 消费 ternary。

    原始:
        {**(a if c else b)}
    缺陷: dict literal 含 **-展开 ternary。BUILD_MAP 0 + DICT_UPDATE 1
         (或 DICT_MERGE) 在 merge_block 中消费 ternary 结果作为 dict 源。
         ternary merge 块的栈输出作为 DICT_UPDATE 的 mapping。可能暴露
         ternary 在 dict literal 内 **-展开位置的归约冲突。
    """
    SOURCE_CODE = """{**(a if c else b)}
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
