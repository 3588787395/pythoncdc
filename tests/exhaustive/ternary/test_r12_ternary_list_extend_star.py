import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryListExtendStar(ExhaustiveTestCase):
    """Bug R12 (new): [*(a if c else b)] — LIST_EXTEND 消费 ternary。

    原始:
        [*(a if c else b)]
    缺陷: list literal 含 *-展开 ternary。BUILD_LIST 0 + LIST_EXTEND 1
         在 merge_block 楚消费 ternary 结果。ternary merge 块的栈输出作为
         LIST_EXTEND 的 iterable 源。可能暴露 ternary 在 list literal 内
         *-展开位置的归约冲突（CALL_FUNCTION_EX 走 BUILD_LIST+LIST_EXTEND+
         LIST_TO_TUPLE 路径，但 list literal 不需 LIST_TO_TUPLE）。
    """
    SOURCE_CODE = """[*(a if c else b)]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
