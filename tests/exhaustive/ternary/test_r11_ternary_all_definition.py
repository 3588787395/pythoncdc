import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryAllDefinition(ExhaustiveTestCase):
    """Bug R11 (new): __all__ definition + ternary list element.

    原始:
        cond = True
        __all__ = ['a', ('b' if cond else 'c'), 'd']
    缺陷: module 级 __all__ 列表内含 ternary 元素。BUILD_LIST 4 + LOAD_CONST
         'a' + ternary merge + LOAD_CONST 'd' + LIST_EXTEND 4 + STORE_NAME
         __all__。ternary merge 块的栈输出作为 LIST_EXTEND 的元素之一，可能
         暴露 ternary consumer 在 list literal 元素槽位的归属冲突。
    """
    SOURCE_CODE = """cond = True
__all__ = ['a', ('b' if cond else 'c'), 'd']
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
