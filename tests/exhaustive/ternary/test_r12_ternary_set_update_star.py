import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernarySetUpdateStar(ExhaustiveTestCase):
    """Bug R12 (new): {*(a if c else b)} — SET_UPDATE 消费 ternary。

    原始:
        {*(a if c else b)}
    缺陷: set literal 含 *-展开 ternary。BUILD_SET 0 + SET_UPDATE 1
         在 merge_block 中消费 ternary 结果作为 set 源。ternary merge
         块的栈输出作为 SET_UPDATE 的 iterable。可能暴露 ternary 在 set
         literal 内 *-展开位置的归约冲突（与 LIST_EXTEND 不同：SET_UPDATE
         不需要 LIST_TO_TUPLE 转换）。
    """
    SOURCE_CODE = """{*(a if c else b)}
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
